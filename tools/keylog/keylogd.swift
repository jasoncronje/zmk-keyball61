// keylogd: records the Keyball61 key log (modules/keylog) into SQLite.
//
// Finds the keyboard's Raw HID interface (usage page 0xFF60, usage 0x61) over
// BLE or USB, keeps asking it to stream, and writes every record to
// ~/Library/Application Support/keyball-keylog/keylog.sqlite with the
// frontmost app. Nothing is kept while macOS Secure Input is on (password
// fields), and nothing is streamed while the pause file exists.
//
// Build: swiftc -O -o keylogd tools/keylog/keylogd.swift
// Run:   ./keylogd            (Ctrl-C stops it and tells the keyboard to stop)
// Pause: touch "$HOME/Library/Application Support/keyball-keylog/paused"

import AppKit
import Carbon
import Foundation
import IOKit.hid
import SQLite3

let usagePage = 0xFF60
let usage = 0x61
let reportSize = 32
let magic: UInt8 = 0x4B
let cmdStop: UInt8 = 0x00
let cmdStart: UInt8 = 0x01
let renewInterval: TimeInterval = 3 // the keyboard's lease is 10 s
let recordSize = 10
let headerSize = 2

let dataDir = FileManager.default.homeDirectoryForCurrentUser
    .appendingPathComponent("Library/Application Support/keyball-keylog")
let dbPath = dataDir.appendingPathComponent("keylog.sqlite").path
let pausePath = dataDir.appendingPathComponent("paused").path

func log(_ message: String) {
    let stamp = ISO8601DateFormatter().string(from: Date())
    FileHandle.standardError.write("\(stamp) \(message)\n".data(using: .utf8)!)
}

// MARK: - Storage

final class Store {
    private var db: OpaquePointer?
    private var insertEvent: OpaquePointer?
    private var insertGap: OpaquePointer?
    private var pending = 0

    init(path: String) {
        try? FileManager.default.createDirectory(at: dataDir, withIntermediateDirectories: true)
        guard sqlite3_open(path, &db) == SQLITE_OK else { fatalError("Can't open \(path)") }
        exec("PRAGMA journal_mode=WAL")
        exec("""
            CREATE TABLE IF NOT EXISTS sessions(
                id INTEGER PRIMARY KEY, started REAL NOT NULL, device TEXT);
            CREATE TABLE IF NOT EXISTS events(
                id INTEGER PRIMARY KEY,
                session INTEGER NOT NULL,
                host_time REAL NOT NULL,  -- Unix seconds when the report arrived
                seq INTEGER NOT NULL,     -- report sequence number, wraps at 256
                kind INTEGER NOT NULL,    -- 1 position, 2 keycode, 3 layer, 4 dropped
                flags INTEGER NOT NULL,   -- bit 0: pressed / layer active
                a INTEGER NOT NULL, b INTEGER NOT NULL, c INTEGER NOT NULL,
                kb_ms INTEGER NOT NULL,   -- keyboard event time, ms since its boot
                app TEXT);
            CREATE INDEX IF NOT EXISTS events_session ON events(session, id);
            CREATE TABLE IF NOT EXISTS gaps(
                session INTEGER, host_time REAL NOT NULL, reason TEXT NOT NULL);
            """)
        sqlite3_prepare_v2(db, """
            INSERT INTO events(session, host_time, seq, kind, flags, a, b, c, kb_ms, app)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, -1, &insertEvent, nil)
        sqlite3_prepare_v2(db, "INSERT INTO gaps(session, host_time, reason) VALUES (?, ?, ?)",
                           -1, &insertGap, nil)
    }

    func exec(_ sql: String) {
        var err: UnsafeMutablePointer<CChar>?
        if sqlite3_exec(db, sql, nil, nil, &err) != SQLITE_OK {
            fatalError("SQLite: \(String(cString: err!))")
        }
    }

    func newSession(device: String) -> Int64 {
        commit()
        var stmt: OpaquePointer?
        sqlite3_prepare_v2(db, "INSERT INTO sessions(started, device) VALUES (?, ?)", -1, &stmt, nil)
        sqlite3_bind_double(stmt, 1, Date().timeIntervalSince1970)
        sqlite3_bind_text(stmt, 2, device, -1, SQLITE_TRANSIENT)
        sqlite3_step(stmt)
        sqlite3_finalize(stmt)
        return sqlite3_last_insert_rowid(db)
    }

    private func begin() {
        if pending == 0 { exec("BEGIN") }
        pending += 1
    }

    func event(session: Int64, seq: UInt8, record: ArraySlice<UInt8>, app: String?) {
        let r = Array(record)
        begin()
        let s = insertEvent
        sqlite3_reset(s)
        sqlite3_bind_int64(s, 1, session)
        sqlite3_bind_double(s, 2, Date().timeIntervalSince1970)
        sqlite3_bind_int(s, 3, Int32(seq))
        sqlite3_bind_int(s, 4, Int32(r[0]))
        sqlite3_bind_int(s, 5, Int32(r[1]))
        sqlite3_bind_int(s, 6, Int32(r[2]))
        sqlite3_bind_int(s, 7, Int32(r[3]))
        sqlite3_bind_int(s, 8, Int32(UInt16(r[4]) | UInt16(r[5]) << 8))
        let ms = UInt32(r[6]) | UInt32(r[7]) << 8 | UInt32(r[8]) << 16 | UInt32(r[9]) << 24
        sqlite3_bind_int64(s, 9, Int64(ms))
        if let app { sqlite3_bind_text(s, 10, app, -1, SQLITE_TRANSIENT) } else { sqlite3_bind_null(s, 10) }
        sqlite3_step(s)
    }

    func gap(session: Int64?, reason: String) {
        begin()
        let s = insertGap
        sqlite3_reset(s)
        if let session { sqlite3_bind_int64(s, 1, session) } else { sqlite3_bind_null(s, 1) }
        sqlite3_bind_double(s, 2, Date().timeIntervalSince1970)
        sqlite3_bind_text(s, 3, reason, -1, SQLITE_TRANSIENT)
        sqlite3_step(s)
    }

    func commit() {
        if pending > 0 {
            exec("COMMIT")
            pending = 0
        }
    }
}

let SQLITE_TRANSIENT = unsafeBitCast(-1, to: sqlite3_destructor_type.self)

// MARK: - Keyboard link

final class Logger {
    let store = Store(path: dbPath)
    let manager = IOHIDManagerCreate(kCFAllocatorDefault, IOOptionBits(kIOHIDOptionsTypeNone))
    var devices: [IOHIDDevice: (session: Int64, buffer: UnsafeMutablePointer<UInt8>, lastSeq: UInt8?)] = [:]
    var frontmostApp: String? = NSWorkspace.shared.frontmostApplication?.bundleIdentifier
    var secureInput = false
    var paused = false

    func start() {
        NSWorkspace.shared.notificationCenter.addObserver(
            forName: NSWorkspace.didActivateApplicationNotification, object: nil, queue: .main
        ) { [weak self] note in
            let app = note.userInfo?[NSWorkspace.applicationUserInfoKey] as? NSRunningApplication
            self?.frontmostApp = app?.bundleIdentifier
        }

        IOHIDManagerSetDeviceMatching(manager, [
            kIOHIDDeviceUsagePageKey: usagePage,
            kIOHIDDeviceUsageKey: usage,
        ] as CFDictionary)
        let context = Unmanaged.passUnretained(self).toOpaque()
        IOHIDManagerRegisterDeviceMatchingCallback(manager, { context, _, _, device in
            Unmanaged<Logger>.fromOpaque(context!).takeUnretainedValue().attach(device)
        }, context)
        IOHIDManagerRegisterDeviceRemovalCallback(manager, { context, _, _, device in
            Unmanaged<Logger>.fromOpaque(context!).takeUnretainedValue().detach(device)
        }, context)
        IOHIDManagerScheduleWithRunLoop(manager, CFRunLoopGetMain(), CFRunLoopMode.defaultMode.rawValue)
        let result = IOHIDManagerOpen(manager, IOOptionBits(kIOHIDOptionsTypeNone))
        if result != kIOReturnSuccess {
            log("Can't open HID manager (0x\(String(result, radix: 16)))")
        }

        Timer.scheduledTimer(withTimeInterval: renewInterval, repeats: true) { [weak self] _ in
            self?.tick()
        }
        Timer.scheduledTimer(withTimeInterval: 1, repeats: true) { [weak self] _ in
            self?.store.commit()
        }
        log("Waiting for the keyboard's Raw HID interface; writing to \(dbPath)")
    }

    func name(of device: IOHIDDevice) -> String {
        let product = IOHIDDeviceGetProperty(device, kIOHIDProductKey as CFString) as? String ?? "?"
        let transport = IOHIDDeviceGetProperty(device, kIOHIDTransportKey as CFString) as? String ?? "?"
        return "\(product) (\(transport))"
    }

    func attach(_ device: IOHIDDevice) {
        let buffer = UnsafeMutablePointer<UInt8>.allocate(capacity: 64)
        let session = store.newSession(device: name(of: device))
        devices[device] = (session, buffer, nil)
        log("Connected: \(name(of: device)), session \(session)")

        let context = Unmanaged.passUnretained(self).toOpaque()
        IOHIDDeviceRegisterInputReportCallback(device, buffer, 64, { context, result, sender, _, _, report, length in
            guard result == kIOReturnSuccess, let sender else { return }
            let device = Unmanaged<IOHIDDevice>.fromOpaque(sender).takeUnretainedValue()
            let bytes = Array(UnsafeBufferPointer(start: report, count: length))
            Unmanaged<Logger>.fromOpaque(context!).takeUnretainedValue().received(bytes, from: device)
        }, context)
        send(paused ? cmdStop : cmdStart, to: device)
    }

    func detach(_ device: IOHIDDevice) {
        guard let entry = devices.removeValue(forKey: device) else { return }
        store.gap(session: entry.session, reason: "disconnected")
        store.commit()
        log("Disconnected: \(name(of: device))")
        // The buffer is left allocated: IOKit may still hold it until the device is released
    }

    func send(_ command: UInt8, to device: IOHIDDevice) {
        var report = [UInt8](repeating: 0, count: reportSize)
        report[0] = magic
        report[1] = command
        let result = IOHIDDeviceSetReport(device, kIOHIDReportTypeOutput, 0, report, report.count)
        if result != kIOReturnSuccess {
            log("Command \(command) to \(name(of: device)) failed (0x\(String(result, radix: 16)))")
        }
    }

    func tick() {
        let nowPaused = FileManager.default.fileExists(atPath: pausePath)
        if nowPaused != paused {
            paused = nowPaused
            log(paused ? "Paused" : "Resumed")
            for (_, entry) in devices {
                store.gap(session: entry.session, reason: paused ? "paused" : "resumed")
            }
        }
        for device in devices.keys {
            send(paused ? cmdStop : cmdStart, to: device)
        }
    }

    func received(_ report: [UInt8], from device: IOHIDDevice) {
        guard report.count >= headerSize, report[0] == magic, var entry = devices[device] else { return }

        let seq = report[1]
        if let last = entry.lastSeq, seq != last &+ 1 {
            store.gap(session: entry.session, reason: "lost reports: seq \(last) -> \(seq)")
        }
        entry.lastSeq = seq
        devices[device] = entry

        let secure = IsSecureEventInputEnabled()
        if secure != secureInput {
            secureInput = secure
            store.gap(session: entry.session, reason: secure ? "secure input on" : "secure input off")
        }
        if secure || paused { return }

        var offset = headerSize
        while offset + recordSize <= report.count {
            let record = report[offset..<offset + recordSize]
            if record[record.startIndex] == 0 { break } // unused slot
            store.event(session: entry.session, seq: seq, record: record, app: frontmostApp)
            offset += recordSize
        }
    }

    func stop() {
        for device in devices.keys {
            send(cmdStop, to: device)
        }
        store.commit()
    }
}

// MARK: - Main

let logger = Logger()
logger.start()

var signalSources: [DispatchSourceSignal] = []
for sig in [SIGINT, SIGTERM] {
    signal(sig, SIG_IGN)
    let source = DispatchSource.makeSignalSource(signal: sig, queue: .main)
    source.setEventHandler {
        logger.stop()
        log("Stopped")
        exit(0)
    }
    source.resume()
    signalSources.append(source)
}

RunLoop.main.run()

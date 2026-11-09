if(CONFIG_KEYBALL61_STATUS_SCREEN)
  target_sources(app PRIVATE src/status_screen.c src/draw.c src/glyphs.c src/layout_common.c)
  # On both halves: the behavior on each, the sender on the right half
  target_sources_ifdef(CONFIG_DT_HAS_ZMK_BEHAVIOR_LAYER_SYNC_ENABLED app PRIVATE src/layer_sync.c)

  if(CONFIG_KEYBALL61_STATUS_SCREEN_NICE_VIEW)
    target_sources(app PRIVATE src/layout_nice_view.c)
  else()
    target_sources(app PRIVATE src/layout_oled.c)
  endif()

  if(NOT CONFIG_ZMK_SPLIT OR CONFIG_ZMK_SPLIT_ROLE_CENTRAL)
    target_sources(app PRIVATE src/central.c)
  else()
    target_sources(app PRIVATE src/peripheral.c)
  endif()
endif()

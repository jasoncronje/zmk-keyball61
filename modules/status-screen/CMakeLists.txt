if(CONFIG_KEYBALL61_STATUS_SCREEN)
  target_sources(app PRIVATE src/status_screen.c src/draw.c src/glyphs.c)

  if(NOT CONFIG_ZMK_SPLIT OR CONFIG_ZMK_SPLIT_ROLE_CENTRAL)
    target_sources(app PRIVATE src/central.c)
  else()
    target_sources(app PRIVATE src/peripheral.c)
  endif()
endif()

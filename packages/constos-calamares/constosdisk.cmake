calamares_add_plugin(constosdisk
    TYPE viewmodule
    EXPORT_MACRO PLUGINDLLEXPORT_PRO
    SOURCES constosdisk.cpp
    LINK_PRIVATE_LIBRARIES ${qtname}::Widgets
    NO_CONFIG
)

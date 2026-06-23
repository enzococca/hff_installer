# -*- coding: utf-8 -*-
"""
HFF Installer Plugin
A QGIS plugin to install and update HFF (Honor Frost Foundation) plugin from GitHub.
"""


def classFactory(iface):
    """Load HFFInstaller class from file hff_installer.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    from .hff_installer import HFFInstaller
    return HFFInstaller(iface)

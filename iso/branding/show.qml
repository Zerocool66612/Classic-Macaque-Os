// Original Macaque Classic installer presentation.
import QtQuick 2.0
import calamares.slideshow 1.0
Presentation {
    id: presentation
    Slide { Image { anchors.fill: parent; fillMode: Image.PreserveAspectFit; source: "slide-desktop.png" } }
    Slide { Image { anchors.fill: parent; fillMode: Image.PreserveAspectFit; source: "slide-terminal.png" } }
    Slide { Image { anchors.fill: parent; fillMode: Image.PreserveAspectFit; source: "slide-linux.png" } }
}

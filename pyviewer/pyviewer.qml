import QtQuick.Controls
import QtQuick

ApplicationWindow {
  id: main
  flags: Qt.Window | Qt.FramelessWindowHint
  title: qsTr("Reviewer Gallery")
  visible: true
  property var layout: [4,1]
  width: 1600
  height: 1000
  Rectangle {
    id: handler
    anchors.fill: parent
    color: "black";
    focus: true
    Keys.enabled: true
    Keys.onEscapePressed: Qt.quit()
  }
  Column {
    id: info
    anchors.right: parent.right
    anchors.left: parent.left
    anchors.top: parent.top
    Image {
      fillMode: Image.PreserveAspectCrop
      width: info.width / 4
      height: info.height
      source: ""
    }
    Text {
      text: qsTr("Hello \n World")
      anchors.centerIn: parent
     }
    Image {
      fillMode: Image.PreserveAspectCrop
      width: info.width / 4
      height: info.height
      source: ""
    }
    Text {
      text: qsTr("Hello \n World")
      anchors.centerIn: parent
     }
  }
  SwipeView {
    id: swipe
    currentIndex: 0
    anchors.right: parent.right
    anchors.left: parent.left
    anchors.bottom: parent.bottom
    property int max_image_count: 20
    property int panels: Math.floor(swipe.max_image_count/(main.layout[0] * main.layout[1]))
    Repeater {
      model: swipe.panels
      Grid {
        rowSpacing: 2
        columnSpacing: 2
        columns: main.layout[0]
        rows: main.layout[1]
        Repeater {
          model: main.layout[0] * main.layout[1];
          Item {
            width: swipe.width / main.layout[0]
            height: swipe.height / main.layout[1]
            Image {
              anchors.fill: parent
              fillMode: Image.PreserveAspectCrop
              sourceSize.width: swipe.width / main.layout[0]
              sourceSize.height: swipe.height / main.layout[1]
              source: ""
            }
          }
        }
      }
    }
    function update_images() {
      for (var i = 0; i < swipe.panels ; i++)  {
        for ( var j = 0; j < main.layout[0] * main.layout[1]; j++ ) {
          var index = j+i*(main.layout[0] * main.layout[1])
          if ( index < viewer.length ) swipe.contentChildren[i].children[j].children[0].source = "data:image;base64," + viewer.images[index]
          else swipe.contentChildren[i].children[j].children[0].source = ""
        }
      }
    }
    Component.onCompleted: {
      viewer.images_changed.connect(swipe.update_images)
      viewer.set_max_image_count(swipe.max_image_count)
    }
  }
}

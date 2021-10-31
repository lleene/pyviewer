import QtQuick.Controls 2.13
import QtQuick.Layouts 1.15
import QtQuick 2.13

ApplicationWindow {
  id: main
  flags: Qt.Window | Qt.FramelessWindowHint
  title: qsTr("Reviewer Gallery")
  visible: true
  visibility: "FullScreen"
  color: "black"
  property var layout: [2,1]
  property int max_image_count: 50
  width: 1600
  height: 1000
  Rectangle {
    id: handler
    anchors.bottom: main.bottom
    anchors.left: main.left
    width: main.width/4
    height: info.height/8
    color: "black";
    focus: true
    Keys.enabled: true
    Keys.onEscapePressed: Qt.quit()
    Keys.onUpPressed: {
      viewer.load_next_archive(1);
      info.currentIndex = 0
    }
    Keys.onDownPressed: {
      viewer.load_next_archive(-1);
      info.currentIndex = 0
    }
    Keys.onLeftPressed: info.currentIndex = info.currentIndex <= 0 ? info.contentChildren.length - 1 : info.currentIndex - 1
    Keys.onRightPressed: info.currentIndex = info.currentIndex >= info.contentChildren.length - 1 ? 0 : info.currentIndex + 1
    Text {
      id: info_text
      anchors.centerIn: parent
      text: ""
      font.pixelSize: 16
      color: "white"
      smooth: true
    }
  }
  SwipeView {
    id: info
    currentIndex: 0
    anchors.fill: parent
    Repeater {
      model: Math.ceil(main.max_image_count/(main.layout[0] * main.layout[1]))
      Grid {
        rowSpacing: 2
        columnSpacing: 2
        columns: main.layout[0]
        rows: main.layout[1]
        Repeater {
          model: main.layout[0] *  main.layout[1]
          Item {
            width: info.width / main.layout[0]
            height: info.height / main.layout[1]
            Image {
              anchors.fill: parent
              fillMode: Image.PreserveAspectCrop
            }
          }
        }
      }
    }
  }
  Component.onCompleted: {
    function update_info() {
      for (var i = 0; i < main.max_image_count ; i++)  {
          var panel = Math.floor(i /(main.layout[0] * main.layout[1]))
          var tile = i % (main.layout[0] * main.layout[1])
          if ( i < viewer.images.length ) info.contentChildren[panel].children[tile].children[0].source = "data:image;base64," + viewer.images[i]
          else info.contentChildren[panel].children[tile].children[0].source = ""
      }
      info_text.text = viewer.file_name
    }
    viewer.images_changed.connect(update_info)
    viewer.set_max_image_count(main.max_image_count)
  }
}

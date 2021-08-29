import QtQuick.Controls 2.13
import QtQuick.Layouts 1.15
import QtQuick 2.13

ApplicationWindow {
  id: main
  flags: Qt.Window | Qt.FramelessWindowHint
  title: qsTr("Reviewer Gallery")
  visible: true
  color: "black"
  property var layout: [4,1]
  property int max_image_count: 20
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
      swipe.currentIndex = 0
    }
    Keys.onDownPressed: {
      viewer.load_next_archive(-1);
      swipe.currentIndex = 0
    }
    Keys.onLeftPressed: info.currentIndex = info.currentIndex <= 0 ? main.max_image_count - 1 : info.currentIndex - 1
    Keys.onRightPressed: info.currentIndex = info.currentIndex >= main.max_image_count - 1 ? 0 : info.currentIndex + 1
    Text {
      id: info_text
      anchors.centerIn: parent
      text: ""
      font.pixelSize: 16
      color: "white"
      smooth: true
    }
  }
  ColumnLayout {
    anchors.fill: parent
    spacing: 0
    SwipeView {
      id: info
      Layout.preferredHeight: main.height / 2
      Layout.preferredWidth: main.width / 2
      Repeater {
        width: info.width / 4
        height: info.height
        model: main.max_image_count
        Item {
          Image {
            width: main.width / 4
            height: main.height / 2
            fillMode: Image.PreserveAspectCrop
            source: ""
          }
        }
      }
    }
    SwipeView {
      id: swipe
      Layout.preferredHeight: main.height / 2
      Layout.fillWidth: true
      Repeater {
        model: main.max_image_count
        Item {
          //width: swipe.width / 4
          //height: swipe.height
          //anchors.centerIn: parent
          Image {
            width: main.width / 4
            height: main.height / 2
            fillMode: Image.PreserveAspectCrop
            source: ""
          }
          /*
          Rectangle {
            color: "black"
            anchors.bottom: parent.bottom
            height: swipe.height/8
            Text {
              anchors.centerIn: parent
              text: ""
              font.pixelSize: 16
              color: "white"
              smooth: true
            }
          }
          */
        }
      }
    }
  }
  Component.onCompleted: {
    function update_info() {
      for (var i = 0; i < main.max_image_count ; i++)  {
          if ( i < viewer.length_images ) info.contentChildren[i].children[0].source = "data:image;base64," + viewer.images[i]
          else info.contentChildren[i].children[0].source = ""
      }
      info_text.text = viewer.file_name
    }
    function update_swipe() { // .children[0]
      for (var i = 0; i < main.max_image_count ; i++)  {
          if ( i < viewer.length_previews ) {
            swipe.contentChildren[i].children[0].source = "data:image;base64," + viewer.previews[i]
            swipe.contentChildren[i].children[1].children[0].text = viewer.meta_data[i]
          }
          else {
            swipe.contentChildren[i].children[0].source = ""
            swipe.contentChildren[i].children[1].children[0].text = ""
          }
      }
    }
    viewer.images_changed.connect(update_swipe)
    viewer.images_changed.connect(update_info)
    viewer.set_max_image_count(main.max_image_count)
  }
}

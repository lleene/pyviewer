import QtQuick.Controls 2.0
import QtQuick 2.0

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
  SwipeView {
    id: info
    anchors.top: parent.top
    height: main.height/2
    width: main.width
    Repeater {
      model: main.max_image_count
      Item {
        width: main.width / main.layout[0]
        height: info.height
        Image {
          anchors.fill: parent
          fillMode: Image.PreserveAspectCrop
          source: ""
        }
      }
    }
    function update_images() {
      for (var i = 0; i < main.max_image_count ; i++)  {
          if ( i < viewer.length_images ) info.contentChildren[i].children[0].source = "data:image;base64," + viewer.images[i]
          else info.contentChildren[i].children[0].source = ""
      }
      info_text.text = viewer.file_name
    }
  }
  Rectangle {
    id: handler
    anchors.bottom: info.bottom
    anchors.left: info.left
    width: main.width / main.layout[0]
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
  SwipeView {
    id: swipe
    anchors.bottom: parent.bottom
    width: main.width
    height: main.height/2
    Repeater {
      model: main.max_image_count
      Item {
        width: main.width / main.layout[0]
        height: swipe.height
        Image {
          width: main.width / main.layout[0]
          height: swipe.height
          fillMode: Image.PreserveAspectCrop
          source: ""
        }
        Rectangle {
          color: "black"
          anchors.bottom: parent.bottom
          width: main.width / main.layout[0]
          height: swipe.height/8
          Text {
            anchors.centerIn: parent
            text: ""
            font.pixelSize: 16
            color: "white"
            smooth: true
          }
        }
      }
    }
    function update_images() { // .children[0]
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
    Component.onCompleted: {
      viewer.images_changed.connect(swipe.update_images)
      viewer.images_changed.connect(info.update_images)
      viewer.set_max_image_count(main.max_image_count)
    }
  }
}

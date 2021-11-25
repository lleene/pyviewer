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
  readonly property int panel_count: 4
  readonly property var layout: [2,1]
  readonly property int tile_count: main.layout[0] * main.layout[1]
  property int index: 0
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
      main.index = 0
      info.update_info(main.index,main.tile_count*2,0)
    }
    Keys.onDownPressed: {
      viewer.load_next_archive(-1);
      info.currentIndex = 0
      main.index = 0
      info.update_info(main.index,main.tile_count*2,0)
    }
    Keys.onLeftPressed: {
      if ( main.index > 0 ) { // avoid negative index on main
        if ( main.index > main.tile_count ) info.update_info(main.index-2*main.tile_count, main.tile_count, info.currentIndex-2)
        info.currentIndex = info.currentIndex <= 0 ? (main.panel_count - 1) : info.currentIndex - 1
        main.index = main.index - main.tile_count
      }
    }
    Keys.onRightPressed: {
      info.update_info(main.index+2*main.tile_count, main.tile_count, info.currentIndex+2)
      info.currentIndex = info.currentIndex >= (main.panel_count - 1) ? 0 : info.currentIndex + 1
      main.index = main.index + main.tile_count
    }
    Text {
      id: info_text
      anchors.centerIn: parent
      text: ""
      font.pixelSize: 16
      color: "white"
      style: Text.Outline;
      styleColor: "black"
      smooth: true
    }
  }
  SwipeView {
    id: info
    currentIndex: 0
    anchors.fill: parent
    Repeater {
      model: main.panel_count
      Grid {
        rowSpacing: 2
        columnSpacing: 2
        columns: main.layout[0]
        rows: main.layout[1]
        Repeater {
          model: main.tile_count
          Item {
            width: info.width / main.layout[0]
            height: info.height / main.layout[1]
            Image {
              anchors.fill: parent
              fillMode: Image.PreserveAspectFit
            }
          }
        }
      }
    }
    function update_info(index_start, image_count, panel_start) {
    var j = 0;
    for (var panel = (main.panel_count + panel_start) % main.panel_count; j < image_count; ) {
      for (var tile = 0; tile < main.tile_count; tile++) {
        viewer.index(j+index_start)
        var data = viewer.image
        data == "" ? info.contentChildren[panel].children[tile].children[0].source = "" : info.contentChildren[panel].children[tile].children[0].source = "data:image;base64," + data
        j++
      }
      panel = (panel + 1) % main.panel_count
    }
    info_text.text = viewer.file_name
    }
  }
  Component.onCompleted: info.update_info(main.index,main.tile_count*2,0)
}

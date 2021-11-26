import QtQuick.Controls 2.13
import QtQuick.Layouts 1.15
import QtQuick 2.15

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
        info.decrementCurrentIndex()
        main.index = main.index - main.tile_count
      }
    }
    Keys.onRightPressed: {
      info.update_info(main.index+2*main.tile_count, main.tile_count, info.currentIndex+2)
      info.incrementCurrentIndex()
      main.index = main.index + main.tile_count
    }
    Keys.onDigit1Pressed:{
        viewer.hash(main.index)
    }
    Keys.onDigit2Pressed:{
        viewer.hash(main.index+1)
    }
    Text {
      id: info_text
      anchors.left: parent.left
      anchors.top: parent.top
      anchors.leftMargin: 10;
      anchors.topMargin: 10;
      text: ""
      font.pixelSize: 24
      color: "white"
      style: Text.Outline;
      styleColor: "black"
      smooth: true
    }
  }
  Component{
      id: path_delegate
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
  PathView {
    id: info
    anchors.fill: parent
    snapMode: PathView.SnapOneItem
    model: main.panel_count
    delegate: path_delegate
    path: Path {
            startX: -info.width / 2  // let the first item in left
            startY: info.height / 2  // item's vertical center is the same as line's
            PathLine {
                relativeX: info.width * main.panel_count  // all items in lines
                relativeY: 0
            }
        }
    function update_info(index_start, image_count, panel_start) {
    var j = 0;
    for (var panel = (main.panel_count + panel_start) % main.panel_count; j < image_count; ) {
      for (var tile = 0; tile < main.tile_count; tile++) {
        viewer.index(j+index_start)
        var data = viewer.image
        if (data == "" ) info.children[1+panel].children[tile].children[0].source = ""
        else info.children[1+panel].children[tile].children[0].source = "data:image;base64," + data
        j++
      }
      panel = (panel + 1) % main.panel_count
    }
    info_text.text = viewer.file_name
    }
  }
  Component.onCompleted: info.update_info(main.index,main.tile_count*2,0)
}

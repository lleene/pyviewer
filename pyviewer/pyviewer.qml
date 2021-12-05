import QtQuick.Controls
import QtQuick.Layouts
import QtQuick

ApplicationWindow {
  id: main
  flags: Qt.Window | Qt.FramelessWindowHint
  title: qsTr("Reviewer Gallery")
  visible: true
  visibility: "FullScreen"
  color: "black"
  readonly property int panel_count: 4
  property var layout: [4,2]
  property int tile_count: main.layout[0] * main.layout[1]
  property int index: 0
  // Adjustable sub-container for aggregating images on a grid
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
              mipmap: true
            }
          }
        }
      }
  }
  // Main container for showing and transitioning through images
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
    for (var panel = (main.panel_count + panel_start + 1) % main.panel_count; j < image_count; ) {
      info.children[1+panel].columns = main.layout[0]
      info.children[1+panel].rows = main.layout[1]
      for (var tile = 0; tile < main.tile_count; tile++) {
        var data = ""
        if(j+index_start >= 0) {
          viewer.index(j+index_start)
          data = viewer.image
        }
        if (data != "") info.children[1+panel].children[tile].children[0].source = "data:image;base64," + data
        else info.children[1+panel].children[tile].children[0].source = ""
        j++
      }
      panel = (panel + 1) % main.panel_count
    }
    info_text.text = viewer.file_name
    }
  }
  Rectangle {
    id: handler
    focus: true
    anchors.left: parent.left
    height: parent.height;
    anchors.leftMargin: 20;
    Keys.enabled: true
    Keys.onEscapePressed: Qt.quit()
    // Default Naviation
    Keys.onUpPressed: {
      viewer.load_next_archive(1);
      info.currentIndex = 0
      main.index = 0
      info.update_info(0,main.tile_count*3,0)
    }
    Keys.onDownPressed: {
      viewer.load_next_archive(-1);
      info.currentIndex = 0
      main.index = 0
      info.update_info(0,main.tile_count*3,0)
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
    // Filter controls
    Keys.onTabPressed: {
      viewer.update_tag_filter(false)
      info.currentIndex = 0
      main.index = 0
      info.update_info(0,main.tile_count*3,0)
    }
    Keys.onSpacePressed: {
      viewer.update_tag_filter(true)
      info.currentIndex = 0
      main.index = 0
      info.update_info(0,main.tile_count*3,0)
    }
    Keys.onDeletePressed: {
      viewer.undo_last_filter()
      info.currentIndex = 0
      main.index = 0
      info.update_info(0,main.tile_count*3,0)
    }
    // Fetch image data relative to index
    Keys.onDigit1Pressed:{viewer.hash(main.index+0)}
    Keys.onDigit2Pressed:{viewer.hash(main.index+1)}
    Keys.onDigit3Pressed:{viewer.hash(main.index+2)}
    Keys.onDigit4Pressed:{viewer.hash(main.index+3)}
    Keys.onDigit5Pressed:{viewer.hash(main.index+4)}
    Keys.onDigit6Pressed:{viewer.hash(main.index+5)}
    Keys.onDigit7Pressed:{viewer.hash(main.index+6)}
    Keys.onDigit8Pressed:{viewer.hash(main.index+7)}
    // Zoom functionality
    Keys.onDigit9Pressed: {
        if(main.layout[0] * main.layout[1] > 1){
            if (main.layout[0] / main.layout[1] >= 2) main.layout[0] = Math.max(main.layout[0] >> 1,1)
            else main.layout[1] = Math.max(main.layout[1] >> 1, 1)
        }
        main.tile_count = main.layout[0] * main.layout[1]
        info.update_info(main.index - main.tile_count, main.tile_count*3, info.currentIndex - 1)
    }
    Keys.onDigit0Pressed: {
        if(main.layout[0] * main.layout[1] < 32){
            if ((2 * main.layout[0] / main.layout[1]) > 2) main.layout[1] = 2 * main.layout[1]
            else main.layout[0] = 2 * main.layout[0]
        }
        main.tile_count = main.layout[0] * main.layout[1]
        info.update_info(main.index - main.tile_count, main.tile_count*3, info.currentIndex - 1)
    }
    // Info text showing current tag
    Text {
      id: info_text
      anchors.top: parent.top
      anchors.topMargin: 20
      text: ""
      font.pixelSize: 24
      color: "white"
      style: Text.Outline;
      styleColor: "black"
      smooth: true
    }
  }
  Component.onCompleted: info.update_info(main.index,main.tile_count*2,0)
}

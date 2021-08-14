import QtQuick.Controls
import QtQuick
// import QtMultimedia not ready in QT6

ApplicationWindow {
  id: main
  flags: Qt.Window | Qt.FramelessWindowHint
  title: qsTr("Reviewer Gallery")
  visible: true
  property var layout: [2,1]
  visibility: Window.FullScreen
  width: 1600
  height: 1000

  Rectangle {
    id: handler
    anchors.fill: parent
    color: "black";
    focus: true
    Keys.enabled: true
    Keys.onEscapePressed: Qt.quit()
    Keys.onLeftPressed: swipe.currentIndex = Math.max(swipe.currentIndex-1,0)
    //Keys.onLeftPressed: swipe.currentIndex = Math.abs((swipe.currentIndex-1)%swipe.panels)
    Keys.onRightPressed: swipe.currentIndex = Math.min(swipe.currentIndex+1,swipe.panels)
    //Keys.onRightPressed: swipe.currentIndex = Math.abs((swipe.currentIndex+1)%swipe.panels)
    Keys.onTabPressed: {
      viewer.update_tag_filter(false);
      swipe.currentIndex = 0
    }
    Keys.onSpacePressed: {
      viewer.update_tag_filter(true);
      swipe.currentIndex = 0
    }
    Keys.onBacktabPressed: {
      viewer.undo_last_filter();
      swipe.currentIndex = 0
    }
    Keys.onUpPressed: {
      viewer.load_next_archive(1);
      swipe.currentIndex = 0
    }
    Keys.onDownPressed: {
      viewer.load_next_archive(-1);
      swipe.currentIndex = 0
    }
    // TODO split is not defined in pyside2
    property var paths: viewer.path.split("::")
    Component.onCompleted: {
      viewer.path_changed.connect(swipe.update_paths)
      viewer.set_max_image_count(swipe.max_image_count)
    }
  }

  SwipeView {
    id: swipe
    currentIndex: 0
    anchors.fill: parent
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
              source: ""
            }
          }
        }
      }
    }

    function update_paths() {
      // TODO this needs a cleanup
      for (var i = 0; i < swipe.panels ; i++)  {
        for ( var j = 0; j < main.layout[0] * main.layout[1]; j++ ) {
          if ( j+i*(main.layout[0] * main.layout[1]) < handler.paths.length ) {
            swipe.contentChildren[i].children[j].children[0].source = handler.paths[j+i*(main.layout[0] * main.layout[1])]
          }
          else {
            swipe.contentChildren[i].children[j].children[0].source = ""
          }
        }
      }
    }
  }
}

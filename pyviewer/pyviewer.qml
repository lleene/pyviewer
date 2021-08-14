import QtQuick.Controls
import QtQuick

ApplicationWindow {
  id: main
  flags: Qt.Window | Qt.FramelessWindowHint
  title: qsTr("Reviewer Gallery")
  visible: true
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
    Keys.onLeftPressed: swipe.currentIndex = (swipe.currentIndex-1)%swipe.panels
    Keys.onRightPressed: swipe.currentIndex = (swipe.currentIndex+1)%swipe.panels
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
    property var paths: viewer.path.split("::")
    Component.onCompleted: viewer.path_changed.connect(swipe.update_paths)
  }

  SwipeView {
    id: swipe
    currentIndex: 0
    anchors.fill: parent
    property int panels: 4
    property var layout: [4,2]
    Repeater {
      model: swipe.panels
      Grid {
        rowSpacing: 2
        columnSpacing: 2
        columns: swipe.layout[0]
        rows: swipe.layout[1]
        Repeater {
          model: swipe.layout[0] * swipe.layout[1];
          Item {
            width: swipe.width / swipe.layout[0]
            height: swipe.height / swipe.layout[1]
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
        for ( var j = 0; j < swipe.layout[0] * swipe.layout[1]; j++ ) {
          if ( j+i*(swipe.layout[0] * swipe.layout[1]) < handler.paths.length ) {
            swipe.contentChildren[i].children[j].children[0].source = handler.paths[j+i*(swipe.layout[0] * swipe.layout[1])]
          }
          else {
            swipe.contentChildren[i].children[j].children[0].source = ""
          }
        }
      }
    }
  }
}

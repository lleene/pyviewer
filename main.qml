import QtQuick.Controls 2.4
import QtQuick 2.1

ApplicationWindow {
  id: main
  flags: Qt.Window | Qt.FramelessWindowHint
  title: qsTr("Reviewer Gallery")
  visible: true
  width: 1600
  height: 1000

  Rectangle {
    anchors.fill: parent
    color: "black";
    focus: true
    Keys.enabled: true
    Keys.onEscapePressed: Qt.quit()
    Keys.onLeftPressed: grid.page = Math.max(grid.page-1,0)
    Keys.onRightPressed: grid.page = Math.min(grid.page+1,4)
    Keys.onTabPressed: viewer.updateTagFilter(false)
    Keys.onSpacePressed: viewer.updateTagFilter(true)
    Keys.onBacktabPressed: viewer.undoLastFilter()
    Keys.onUpPressed: {
      viewer.loadNextArchive(1);
      grid.page = 0
    }
    Keys.onDownPressed: {
      viewer.loadNextArchive(-1);
      grid.page = 0
    }
  }

  Grid {
    id: grid;
    property int page: 0
    anchors.fill: parent
    rowSpacing: 5
    columnSpacing: 5
    columns: 4
    rows: 2
    property var paths: viewer.path.split(" ")

    Repeater {
      id: repeater
      model: grid.columns * grid.rows;
      delegate: delegateGridImage
    }
    Component {
      id: delegateGridImage
      Item {
        property int currentColumn: index % grid.columns
        property int currentRow: Math.floor(index / grid.rows);
        width: grid.width / grid.columns
        height: grid.height / grid.rows
        Image {
          anchors.fill: parent
          fillMode: Image.PreserveAspectCrop
          source: index+grid.page*(grid.rows*grid.columns) >= grid.paths.length ?  "" : grid.paths[index+grid.page*(grid.rows*grid.columns)]
        }
      }
    }
  }
}

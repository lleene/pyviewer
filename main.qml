import QtQuick.Controls 2.4
import QtQuick 2.1

ApplicationWindow {
  flags: Qt.Window | Qt.FramelessWindowHint 
  title: "Reviewer Gallery"
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
    Keys.onRightPressed: grid.page = Math.min(grid.page+1,10)
  }

  Grid {
    id: grid;
    property int page: 0
    anchors.fill: parent
    rowSpacing: 5
    columnSpacing: 5
    columns: 4
    rows: 2

    Repeater {
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
          source: "data/image" + ( index + grid.page*grid.columns*grid.rows ) + ".png"
        }
      }
    }
  }
}

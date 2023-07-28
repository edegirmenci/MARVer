# -*- coding: utf-8 -*-
"""
A module containing ``NodeEditorWidget`` class
"""
import os
import sys
from qtpy.QtCore import Qt, QPoint
from qtpy.QtGui import QBrush, QPen, QFont, QColor
from qtpy.QtWidgets import QWidget, QVBoxLayout, QApplication, QMessageBox, QLabel, QGraphicsItem, QTextEdit, QPushButton

from include.marver_m.UppaalVisual.nodeeditor.node_scene import Scene, InvalidFile
from include.marver_m.UppaalVisual.nodeeditor.node_node import Node
from include.marver_m.UppaalVisual.nodeeditor.node_edge import Edge, EDGE_TYPE_BEZIER
from include.marver_m.UppaalVisual.nodeeditor.node_graphics_view import QDMGraphicsView
from include.marver_m.UppaalVisual.nodeeditor.utils import dumpException

from include.marver_m.UppaalVisual.xmlToNode import getNodeEdgeList

class NodeEditorWidget(QWidget):
    Scene_class = Scene
    GraphicsView_class = QDMGraphicsView

    """The ``NodeEditorWidget`` class"""
    def __init__(self, parent:QWidget=None):
        """
        :param parent: parent widget
        :type parent: ``QWidget``

        :Instance Attributes:

        - **filename** - currently graph's filename or ``None``
        """
        super().__init__(parent)
        self.filename = None
        self.tempList = []
        self.templateCount = 0

    def setModel(self, _tempList):
        self.tempList = _tempList
        self.templateCount = self.tempList.__len__()
        self.initUI()

    def initUI(self):
        """Set up this ``NodeEditorWidget`` with its layout,  :class:`~nodeeditor.node_scene.Scene` and
        :class:`~nodeeditor.node_graphics_view.QDMGraphicsView`"""
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        # crate graphics scene
        self.scene = self.__class__.Scene_class()

        # create graphics view
        self.view = self.__class__.GraphicsView_class(self.scene.grScene, self)
        self.layout.addWidget(self.view)

    def updateNodeEdgeList(self, fileName):
        self.tempList = getNodeEdgeList(fileName)

    def isModified(self) -> bool:
        """Has the `Scene` been modified?

        :return: ``True`` if the `Scene` has been modified
        :rtype: ``bool``
        """
        return self.scene.isModified()

    def isFilenameSet(self) -> bool:
        """Do we have a graph loaded from file or are we creating a new one?

        :return: ``True`` if filename is set. ``False`` if it is a new graph not yet saved to a file
        :rtype: ''bool''
        """
        return self.filename is not None

    def getSelectedItems(self) -> list:
        """Shortcut returning `Scene`'s currently selected items

        :return: list of ``QGraphicsItems``
        :rtype: list[QGraphicsItem]
        """
        return self.scene.getSelectedItems()

    def hasSelectedItems(self) -> bool:
        """Is there something selected in the :class:`nodeeditor.node_scene.Scene`?

        :return: ``True`` if there is something selected in the `Scene`
        :rtype: ``bool``
        """
        return self.getSelectedItems() != []

    def canUndo(self) -> bool:
        """Can Undo be performed right now?

        :return: ``True`` if we can undo
        :rtype: ``bool``
        """
        return self.scene.history.canUndo()

    def canRedo(self) -> bool:
        """Can Redo be performed right now?

        :return: ``True`` if we can redo
        :rtype: ``bool``
        """
        return self.scene.history.canRedo()

    def getUserFriendlyFilename(self) -> str:
        """Get user friendly filename. Used in the window title

        :return: just a base name of the file or `'New Graph'`
        :rtype: ``str``
        """
        name = os.path.basename(self.filename) if self.isFilenameSet() else "New Graph"
        return name + ("*" if self.isModified() else "")

    def fileNew(self):
        """Empty the scene (create new file)"""
        self.scene.clear()
        self.filename = None
        self.scene.history.clear()
        self.scene.history.storeInitialHistoryStamp()

    def fileLoad(self, filename:str):
        """Load serialized graph from JSON file

        :param filename: file to load
        :type filename: ``str``
        """
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            self.scene.loadFromFile(filename)
            self.filename = filename
            self.scene.history.clear()
            self.scene.history.storeInitialHistoryStamp()
            return True
        except FileNotFoundError as e:
            dumpException(e)
            QMessageBox.warning(self, "Error loading %s" % os.path.basename(filename), str(e).replace('[Errno 2]',''))
            return False
        except InvalidFile as e:
            dumpException(e)
            # QApplication.restoreOverrideCursor()
            QMessageBox.warning(self, "Error loading %s" % os.path.basename(filename), str(e))
            return False
        finally:
            QApplication.restoreOverrideCursor()


    def fileSave(self, filename:str=None):
        """Save serialized graph to JSON file. When called with an empty parameter, we won't store/remember the filename.

        :param filename: file to store the graph
        :type filename: ``str``
        """
        if filename is not None: self.filename = filename
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.scene.saveToFile(self.filename)
        QApplication.restoreOverrideCursor()
        return True

    def addNodes(self, index):
        self.fileNew()

        xMax, xMin, yMax, yMin = \
            self.tempList[index].nodeList[0].x, self.tempList[index].nodeList[0].x, \
            self.tempList[index].nodeList[0].y, self.tempList[index].nodeList[0].y

        localNodes = []
        localEdges = []

        tempIndex = index
        stId = self.tempList[tempIndex].nodeList[0].id
        for i in range(self.tempList[tempIndex].nodeList.__len__()):
            localNodes.append(Node(self.scene, self.tempList[tempIndex].nodeList[i].name,
                                   self.tempList[tempIndex].nodeList[i].namex, self.tempList[tempIndex].nodeList[i].namey,
                                   inputs=[], outputs=[1]))
            localNodes[i].setPos(self.tempList[tempIndex].nodeList[i].x, self.tempList[tempIndex].nodeList[i].y)
            if xMax < self.tempList[tempIndex].nodeList[i].x:
                xMax = self.tempList[tempIndex].nodeList[i].x
            if xMin > self.tempList[tempIndex].nodeList[i].x:
                xMin = self.tempList[tempIndex].nodeList[i].x
            if yMax < self.tempList[tempIndex].nodeList[i].y:
                yMax = self.tempList[tempIndex].nodeList[i].y
            if yMin > self.tempList[tempIndex].nodeList[i].y:
                yMin = self.tempList[tempIndex].nodeList[i].y

        for i in range(self.tempList[tempIndex].edgeList.__len__()):
            localEdges.append(Edge(self.scene, self.tempList[tempIndex].edgeList[i].labelList,
                                   localNodes[self.tempList[tempIndex].edgeList[i].src - stId].outputs[0],
                                   localNodes[self.tempList[tempIndex].edgeList[i].tgt - stId].outputs[0],
                                   self.tempList[tempIndex].edgeList[i].nails, edge_type=1))

        self.view.centerOn(QPoint((xMax + xMin) / 2, (yMax + yMin) / 2))
        self.scene.history.storeInitialHistoryStamp()

    def addCustomNode(self, x, y):
        """Testing method to create a custom Node with custom content"""
        from nodeeditor.node_content_widget import QDMNodeContentWidget
        from nodeeditor.node_serializable import Serializable

        class NNodeContent(QLabel):  # , Serializable):
            def __init__(self, node, parent=None):
                super().__init__("FooBar")
                self.node = node
                self.setParent(parent)

        class NNode(Node):
            NodeContent_class = NNodeContent

        self.scene.setNodeClassSelector(lambda data: NNode)
        node = NNode(self.scene, "CENTER" + str(x) + " " + str(y), inputs=[0, 1, 2])
        node.setPos(x, y)


    def addDebugContent(self):
        """Testing method to put random QGraphicsItems and elements into QGraphicsScene"""
        greenBrush = QBrush(Qt.green)
        outlinePen = QPen(Qt.black)
        outlinePen.setWidth(2)

        rect = self.grScene.addRect(-100, -100, 80, 100, outlinePen, greenBrush)
        rect.setFlag(QGraphicsItem.ItemIsMovable)

        text = self.grScene.addText("This is my Awesome text!", QFont("Ubuntu"))
        text.setFlag(QGraphicsItem.ItemIsSelectable)
        text.setFlag(QGraphicsItem.ItemIsMovable)
        text.setDefaultTextColor(QColor.fromRgbF(1.0, 1.0, 1.0))


        widget1 = QPushButton("Hello World")
        proxy1 = self.grScene.addWidget(widget1)
        proxy1.setFlag(QGraphicsItem.ItemIsMovable)
        proxy1.setPos(0, 30)


        widget2 = QTextEdit()
        proxy2 = self.grScene.addWidget(widget2)
        proxy2.setFlag(QGraphicsItem.ItemIsSelectable)
        proxy2.setPos(0, 60)


        line = self.grScene.addLine(-200, -200, 400, -100, outlinePen)
        line.setFlag(QGraphicsItem.ItemIsMovable)
        line.setFlag(QGraphicsItem.ItemIsSelectable)


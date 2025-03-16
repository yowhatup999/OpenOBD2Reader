STYLE_MAIN = """
/* Haupt-Hintergrund */
QWidget {
    background-color: rgb(22, 22, 22);
    color: white;
    font-family: Helvetica, Arial, sans-serif;
    font-size: 14px;
}

/* Hauptanzeige - Wertebereich mit Rahmen */
#frameStatus, #frameButtons, #logFrame, #frameValues {
    background-color: rgba(30, 30, 30, 0.5);
    border: 2px solid rgba(138, 43, 226, 0.4);
    border-radius: 12px;  
    padding: 10px;
}

/* Button-Leiste (Unten) */
#frameButtons {
    background-color: rgba(30, 30, 30, 0.6);
    border-radius: 15px;
    padding: 8px;
}

/* Button-Styles */
QPushButton {
    background-color: rgba(30, 30, 30, 0.8);
    border: 2px solid rgba(138, 43, 226, 0.4);
    border-radius: 8px;
    padding: 8px 12px;
    color: white;
    font-size: 14px;
}

QPushButton:hover {
    background-color: qlineargradient(
        spread:pad, x1:0, y1:0, x2:1, y2:0,
        stop:0 rgba(138, 43, 226, 0.6),
        stop:0.5 rgba(255, 20, 147, 0.6),
        stop:1 rgba(30, 144, 255, 0.6)
    );
    border: 2px solid rgba(255, 20, 147, 0.7);
}

/* Label Styles für Werte */
QLabel#valueLabel {
    background: rgba(40, 40, 40, 0.6);
    color: white;
    border-radius: 10px;
    padding: 15px;
    border: 2px solid rgba(138, 43, 226, 0.4);
    font-size: 16px;
    font-weight: bold;
}

/* Tooltips */
QToolTip {
    background-color: rgb(50, 50, 50);
    color: white;
    border: 1px solid white;
}
"""
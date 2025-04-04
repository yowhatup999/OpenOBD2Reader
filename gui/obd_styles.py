STYLE_MAIN = """
/* Hintergrund */
QWidget {
    background-color: rgb(22, 22, 22);
    color: white;
    font-family: Helvetica, Arial, sans-serif;
    font-size: 14px;
}

/* Frames ohne sichtbare Qt-Border, da GlowingAnimatedFrame übernimmt */
#frameStatus, #frameButtons, #frameValues, #logFrame {
    background-color: rgba(30, 30, 30, 0.6);
    border: none;
    border-radius: 12px;
    padding: 10px;
}


/* Button-Stil */
QPushButton {
    background-color: rgba(30, 30, 30, 0.9);
    border: 2px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 8px 12px;
    color: white;
    font-size: 14px;
}

QPushButton:hover {
    background-color: rgba(255, 255, 255, 0.05);
    border: 2px solid rgba(255, 255, 255, 0.2);
}

/* Labels für Werteanzeige */
QLabel#valueLabel {
    background: rgba(40, 40, 40, 0.6);
    color: white;
    border-radius: 10px;
    padding: 15px;
    border: 2px solid rgba(255, 255, 255, 0.05);
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

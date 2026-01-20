from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QWidget, QVBoxLayout, QPushButton, QFileDialog
from PyQt5.QtGui import QRegExpValidator, QIntValidator
from PyQt5.QtCore import QRegExp
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from CEQTool import CEQTool
import sys

class CEQToolWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("CEQ_grapher.ui", self)

        # Extra course row widgets are invisible by default
        self.widget_2.setVisible(False)
        self.widget_3.setVisible(False)
        self.visible_rows = 1
        
        # Button actions
        self.addCourseButton.clicked.connect(self.add_course_row)
        self.removeCourseButton.clicked.connect(self.remove_course_row)
        self.plotGraphsButton.clicked.connect(self.plot_graphs)

        # Exclusive and uncheckable checkboxes for Pass rate
        self.amountBox.clicked.connect(lambda: self.exclusive_checkboxes(self.amountBox, self.percentageBox))
        self.percentageBox.clicked.connect(lambda: self.exclusive_checkboxes(self.percentageBox, self.amountBox))

        # Grey out std checkboxes if mean isn't checked
        self.mean_cb = [
            self.meanTeaching,
            self.meanGoals,
            self.meanAssessment,
            self.meanWorkload,
            self.meanImportance,
            self.meanSatisfaction,
        ]

        self.std_cb = [
            self.stdTeaching,
            self.stdGoals,
            self.stdAssessment,
            self.stdWorkload,
            self.stdImportance,
            self.stdSatisfaction,
        ]

        for mean, std in zip(self.mean_cb, self.std_cb):
            std.setEnabled(False)
            mean.stateChanged.connect(
                lambda _, m=mean, s=std: self.toggle_std(m, s)
            )

        # Get text input objects
        self.course_edit = [None]*3
        self.period_edit = [None]*3
        self.start_edit = [None]*3
        self.end_edit = [None]*3

        for i in range(3):
            self.course_edit[i] = getattr(self, f"courseCode_{i+1}")
            self.period_edit[i] = getattr(self, f"studyPeriod_{i+1}")
            self.start_edit[i] = getattr(self, f"startYear_{i+1}")
            self.end_edit[i] = getattr(self, f"endYear_{i+1}")

            # Automatically change to uppercase letters
            self.course_edit[i].textChanged.connect(
                lambda text, le=self.course_edit[i]: le.setText(text.upper())
                )
            
        # Set validators for text inputs
        for i in range(3):
            self.course_edit[i].setValidator(QRegExpValidator(QRegExp(r"[A-Za-z0-9]{6}"), self))
            self.start_edit[i].setValidator(QIntValidator(2003, 2026))
            self.end_edit[i].setValidator(QIntValidator(2003, 2026))

    # Add course code row
    def add_course_row(self):
        if self.visible_rows >= 3:
            return
        
        if self.visible_rows == 1:
            self.widget_2.setVisible(True)
        elif self.visible_rows == 2:
            self.widget_3.setVisible(True)
        
        self.visible_rows += 1

    # Remove added course code row
    def remove_course_row(self):
        if self.visible_rows <= 1:
            return

        if self.visible_rows == 3:
            self.widget_3.setVisible(False)
        elif self.visible_rows == 2:
            self.widget_2.setVisible(False)

        self.visible_rows -= 1

    def exclusive_checkboxes(self, clicked, other):
        if clicked.isChecked():
            other.setChecked(False)

    def toggle_std(self, mean_cb, std_cb):
        if mean_cb.isChecked():
            std_cb.setEnabled(True)
        else:
            std_cb.setChecked(False)
            std_cb.setEnabled(False)
    
    def check_valid_inputs(self):
        year_spans = []
        for i in range(self.visible_rows):
            state,_,_ = self.course_edit[i].validator().validate(self.course_edit[i].text(), 0)
            if state != QIntValidator.Acceptable:
                QMessageBox.warning(self, "Invalid Course", "Please enter a valid course code.")
                return -1

            start = self.start_edit[i].text()
            end = self.end_edit[i].text()
            state1,_,_ = self.start_edit[i].validator().validate(start, 0)
            state2,_,_ = self.end_edit[i].validator().validate(end, 0)
            if state1 != QIntValidator.Acceptable or state2 != QIntValidator.Acceptable:
                QMessageBox.warning(self, "Invalid Year", "Please enter a valid year between 2003 and 2026.")
                return -1
            if int(start) > int(end):
                QMessageBox.warning(self, "Invalid Span", "Please enter the year span correctly")
                return -1
            year_spans.append((int(start), int(end)))

        # Check for year overlap
        for i in range(len(year_spans)):
            for j in range(i+1, len(year_spans)):
                start1, end1 = year_spans[i]
                start2, end2 = year_spans[j]
                if start1 <= end2 and start2 <= end1:
                    QMessageBox.warning(self, "Year Overlap", 
                                        f"Year spans {start1}-{end1} and {start2}-{end2} overlap.")
                    return -1
    
    def get_inputs(self):
        input_list = []
        for i in range(self.visible_rows):
            input_list.append([self.course_edit[i].text(),
                               self.period_edit[i].currentText(),
                               self.start_edit[i].text(),
                               self.end_edit[i].text()])
        # Sort year spans
        input_list.sort(key=lambda x: x[2])

        # Pass rate box
        if self.amountBox.isChecked():
            cb = [1]
        elif self.percentageBox.isChecked():
            cb = [2]
        else:
            cb = [0]
        
        # Remaining boxes
        for mean_chk, std_chk in zip(self.mean_cb, self.std_cb):
            if mean_chk.isChecked():
                if std_chk.isChecked():
                    cb.append(2)
                else:
                    cb.append(1)
            else:
                cb.append(0)
        
        settings = {'Antal godkända/andel av registrerade': cb[0], 
                'God undervisning': cb[1],
                'Tydliga mål': cb[2],
                'Förståelseinriktad examination': cb[3],
                'Lämplig arbetsbelastning': cb[4],
                'Kursen känns angelägen för min utbildning': cb[5],
                'Överlag är jag nöjd med den här kursen': cb[6]}
        
        return input_list, settings

    # Get data and plot graphs
    def plot_graphs(self):
        if self.check_valid_inputs() == -1:
            return
        input_list, settings = self.get_inputs()
        tool = CEQTool(input_list, settings)
        if tool.webscrape_done == False:
            QMessageBox.warning(self, "Warning", "No data has been found. Check inputs for mistakes.")
        else:
            self.windows = []
            for fig in tool.figs:
                win = PlotWindow(fig)
                self.windows.append(win)

class PlotWindow(QMainWindow):
    def __init__(self, fig):
        super().__init__()

        self.resize(1400, 1000) 
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Add the figure as a canvas
        canvas = FigureCanvas(fig)
        layout.addWidget(canvas)

        save_button = QPushButton("Save Plot")
        save_button.clicked.connect(lambda: self.save_plot(fig))
        layout.addWidget(save_button)

        self.show()

    def save_plot(self, fig):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Plot", "", "PNG Files (*.png);;All Files (*)"
        )
        if file_path:
            fig.savefig(file_path)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CEQToolWindow()
    window.show()
    sys.exit(app.exec_())
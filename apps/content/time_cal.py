import math
# import cv2
from PyPDF2 import PdfFileReader
import pafy
import pytesseract
import time
# import matplotlib.pyplot as plt


def TextTime(text):
    """
    TEXT READ TIME DURATION

    Nothing to install for getting read time of text
    """
    # time = math.floor((len(striphtml(data))/5)/150)
    text = len(text)-text.count(" ")
    # 5 letter makes 1 word and 150 is the average human reading speed in 1 minute
    duration = math.ceil((text/5)/150)
    return (1 if duration < 1 else duration)  # we can use this if we don't want to show 0 minute
    # return ("letters are {} Read Time {} minutes".format(text, duration))


def LinkTime(link):
    """
    YOUTUBE LINK VIDEO VIEW TIME DURATION

    pip install youtube_dl
    then
    pip install pafy
    then in pafy module go to the backend_youtube_dl.py file and on line
    53        self._likes = self._ydl_info.get('like_count',0)
    54        self._dislikes = self._ydl_info.get('dislike_count',0)
    update this lines.
    """

    # link = "https://www.youtube.com/watch?v=nClRnh9BLEc"

    # duration = (pafy.new(data).duration).split(":")

    # Here I have used pafy for connecting to the Youtube link and getting all the details
    duration = (pafy.new(link).duration).split(":")
    # Here time is coming HH:MM:SS So I have added 1 minute extra to in places of counting the seconds.
    time = (int(duration[0])*60)+int(duration[1])+1
    return time


def videoTime():
    """
    UPLOADED LOCAL VIDEO VIEW TIME DURATION

    pip install opencv-python
    """
    cap = cv2.VideoCapture("/home/vicky/Pictures/file_example_MP4_480_1_5MG.mp4")
    if cap.isOpened() == False:
        return ("Error in opening the vidoe file")
    else:
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration_minutes = math.ceil((frame_count//fps)/60)
        duration_seconds = (frame_count//fps) % 60
        return ("fps {} frame_count {} duration {} minute {} seconds".format(fps, frame_count, duration_minutes, duration_seconds))


def PDFTime():
    """
    UPLOADED LOCAL PDF READ TIME DURATION

    pip install PyPDF2
    """
    text = ""
    pdfFileObject = open("/home/vicky/Pictures/Get_Started_With_Smallpdf.pdf", 'rb')
    read = PdfFileReader(pdfFileObject)
    for i in range(0, read.numPages):
        page = read.getPage(i)
        text += page.extractText()
    text = len(text)-text.count(" ")
    duration = math.floor((text/5)/150)
    return (1 if duration < 1 else duration)  # we can use this if we don't want to show 0 minute
    return ("Read Time {} minutes".format(duration))


def ImageTime():
    img = cv2.imread("/home/vicky/Desktop/AtPace_Images/download.png")
    # plt.imshow(img[:,:,::-1])
    # sr = cv2.dnn_superres.DnnSuperResImpl_create()
    # path = "EDSR_x4.pb"
    # sr.readModel(path)
    # sr.setModel("edsr",4)
    # result = sr.upsample(img)
    # plt.imshow(result[:,:,::-1])
    # return plt.show()
    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    threshold_img = cv2.threshold(gray_img, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    cv2.imshow("threshold image", threshold_img)
    time.sleep(10)
    text = pytesseract.image_to_string(threshold_img)
    text = len(text)-text.count(" ")
    # data = pytesseract.image_to_data(img)
    duration = math.ceil((len(text)/5)/120)
    return ("{} Read Time {} minutes".format(text, duration))
    # return ("{} \n\n {}".format(text, data))

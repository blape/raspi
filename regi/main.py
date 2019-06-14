"""Self-service register demo"""

import os, cv2, time
import tkinter as tk 
from tkinter.font import Font
from edgetpu.classification.engine import ClassificationEngine
from PIL import Image, ImageTk

# init Tk window
tk_root = tk.Tk()
tk_root.title('Self-service Register with RasPi + Edge TPU')
tk_root.attributes("-fullscreen", True)
tk_cam = tk.Canvas(tk_root, width=640, height=480)
tk_cam.grid(row=0, column=0, rowspan=2, padx=10, pady=55)
tk_font = Font(family='Courier', size=18)

# product buttons frame
tk_buttons_frame = tk.Frame(tk_root, padx=20, pady=20, 
  width=350, height=230)
tk_buttons_frame.grid(row=0, column=1)
tk_buttons_frame.propagate(False)

# cart items frame
tk_items_frame = tk.Frame(tk_root)
tk_items_frame.grid(row=1, column=1)
tk_items = tk.Listbox(tk_items_frame, height=5, width=22, \
  font=tk_font)
tk_items.pack(side=tk.TOP)

# total price
total_price = 0 
tk_total_price = tk.StringVar()
def update_total_price():
  global total_price
  tk_total_price.set('Total: {0:>6}'.format(str(total_price)))
  print(total_price)
update_total_price()

# checkout
def checkout():
  global total_price
  total_price = 0
  update_total_price()
  tk_items.delete(0, tk.END)
 
# checkout frame
tk_cout_frame = tk.Frame(tk_items_frame, padx=20, pady=20) 
tk_cout_frame.pack(side=tk.TOP)
tk_total = tk.Label(tk_cout_frame, font=tk_font,
  textvariable=tk_total_price)
tk_total.pack(side=tk.LEFT, ipadx=10)
tk_cout_btn = tk.Button(tk_cout_frame, font=tk_font,
  text='Check', height=2, command=checkout)
tk_cout_btn.pack(side=tk.LEFT, ipadx=10)

# init camera
cam = cv2.VideoCapture(0)

# init Edge TPU with TF Lite model
tpu = ClassificationEngine('/home/pi/model.tflite')

# init labels
labels = ['blouse','blouson','cardigan','check shirt','coat','color shirt','down coat','down jacket','down vest','dress','duffle coat','hoodie','jacket','jacket for ladies','knit vest','no sleeve shirt','pants','patterned shirt','polo shirt','school sailor','school suit','shirt','skirt','striped shirt','suit','suit for ladies','sweater','sweater highneck','tie','trench coat','tshirt','vest','wool jacket']

prices = [600,900,600,600,1900,600,3700,2100,1600,3600,1900,900,1230,1230,600,600,670,600,600,1250,1200,350,600,600,1900,1900,600,600,450,1900,600,670,2100]

prices_by_label = {}
for i in range(len(labels)):
  prices_by_label[labels[i]] = prices[i]

# load images
label_images = {}
for l in labels:
  p = 'img/' + l + '.png' 
  if os.path.exists(p):
    label_images[l] = ImageTk.PhotoImage(Image.open(p))
    print('loaded: ' + p)
blank_img = ImageTk.PhotoImage(Image.open('img/blank.png'))

# create button handlers
def create_handler(label):
  def handler():
    global total_price
    price = prices_by_label[label] 
    item_label = ' {0:15.15}{1:>5d} '.format(label, price) 
    tk_items.insert(tk.END, item_label)
    tk_items.see(tk.END)
    total_price = total_price + price 
    update_total_price() 
  return handler
 
# init label buttons
label_buttons = {}
label_detected_times = {}
for l in labels:
  img = label_images[l] if l in label_images else blank_img 
  fr = tk.Frame(tk_buttons_frame, padx=10) 
  cvs = tk.Canvas(fr, width=119, height=100) 
  cvs.pack(side=tk.LEFT)
  cvs.create_image(0, 0, image=img, anchor='nw')
  b = tk.Button(fr, font=tk_font, text=l, height=2, width=10, \
    command=create_handler(l))
  b.pack(side=tk.LEFT)
  label_buttons[l] = fr

# main
def main():

  # main loop 
  while True:

    # tk update
    tk_root.update_idletasks()
    tk_root.update()

    # capture
    r, img_cam = cam.read()
    img_pil = Image.fromarray(img_cam) 
    img_tk = ImageTk.PhotoImage(img_pil)
    tk_cam.create_image(0, 0, image=img_tk, anchor='nw')

    # classification with tpu
    i, score = tpu.ClassifyWithImage(img_pil, top_k=1)[0]
    label = labels[i]
    # print(label + ": " + str(score))

    # record a timestamp for the detected label
    now = time.time()
    if score > 0.5:
      label_detected_times[label] = now

    # show or hide label buttons
    count = 0
    for l in labels:
      is_visible = label_buttons[l].winfo_ismapped()
      if is_visible:
        count = count + 1
      is_detected = now - label_detected_times[l] < 1.0 \
        if l in label_detected_times else False
      if count < 2 and not is_visible and is_detected: 
        label_buttons[l].pack(side=tk.TOP)
      elif is_visible and not is_detected: 
        label_buttons[l].pack_forget()

if __name__ == '__main__':
  main()


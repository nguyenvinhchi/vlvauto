


from tkinter import Tk
from imageutil import text_reader


if __name__=="__main__":
    print('hello')
    # in_file = "images/input/vlv-DuongChau-smallmap_2.png"
    # in_file = "images/input/vlv-LDQ-smallmap_1.png"
    in_file = "images/input/vlv-LDQ-fullmap_1.png"
    # in_file = "images/input/vlv-stuck-buying-med_shop_1.png"
    # in_file = "images/input/vlv-stuck-buying-med-bag_1.png"

    # out_file = f"images/output/vlv-DuongChau-smallmap_2_masked.png"
    out_file = f"images/output/vlv-LDQ-fullmap_1_masked.png"
    # out_file = f"images/output/vlv-LDQ-smallmap_1_masked.png"
    # text_reader.read_text(in_file, out_file)
    
    # Run app
    root = Tk()
    app = text_reader.HSVColorPickerApp(root, in_file, out_file)
    root.mainloop()
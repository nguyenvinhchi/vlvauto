


from tkinter import Tk
from imageutil import text_reader


if __name__=="__main__":
    print('hello')
    # in_file = "images/input/vlv-DuongChau-smallmap_2.png"
    # in_file = "images/input/vlv-LDQ-smallmap_1.png"
    # in_file = "images/input/vlv-LDQ-fullmap_1.png"
    # in_file = "images/input/vlv-stuck-buying-med_shop_1.png"
    # in_file = "images/input/vlv-stuck-buying-med-bag_1.png"
    # in_file = "images/input/vlv-stuck-buying-med-shop_2.png"
    # in_file = "images/input/bluestack/vlv-medicine-shop-truecolor.png"
    # in_file = "images/input/bluestack/vlv-duongchau-smallmap-truecolor-1.png"
    in_file = "images/input/bluestack/vlv-duongchau-smallmap-truecolor-2.png"

    out_file = f"images/output/vlv-duongchau-smallmap-2-masked.png"
    # out_file = f"images/output/vlv-medicine-shop-masked.png"
    # out_file = f"images/output/vlv-stuck-buying-med-bag_2_masked.png"
    # out_file = f"images/output/vlv-stuck-buying-med-shop_2_masked.png"
    # out_file = f"images/output/vlv-LDQ-fullmap_1_masked.png"
    # out_file = f"images/output/vlv-LDQ-smallmap_1_masked.png"
    # text_reader.read_text(in_file, out_file)
    
    # Run app
    root = Tk()
    app = text_reader.HSVColorPickerApp(root, in_file, out_file)
    root.mainloop()
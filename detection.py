def loading_models():
  from keras.models import load_model
  food_or_not_food_model = load_model("./models/food_or_not_food_classifier.h5")
  healthy_junk_indian_model = load_model("./models/healthy_junk_indian_classifier.h5")
  fruits_vegetables_model = load_model("./models/healthy_fruits_vegetables_classifier.h5")
  indian_foods_model = load_model("./models/indian_foods_classifer.h5")

  return food_or_not_food_model,healthy_junk_indian_model,fruits_vegetables_model,indian_foods_model

def prediction(path,food_or_not_food_model,healthy_junk_indian_model,fruits_vegetables_model,indian_foods_model):
  import numpy as np
  from tensorflow.keras.utils import img_to_array,load_img
  from keras.applications.mobilenet_v2 import preprocess_input
  from query import query

  ref = {0:"yes", 1: "no"}
  ref1 = {0: 'Healthy Food', 1: 'Indian Food', 2: 'Junk Food'}
  healthy_foods = {0: "apple",1: "banana",2: "beetroot",3: "bell pepper",4: "cabbage",5: "capsicum",6: "carrot",7: "cauliflower",8: "chilli pepper",9: "corn",10: "cucumber",11: "eggplant",12: "garlic",13: "ginger",14: "grapes",15: "kiwi",16: "lemon",17: "lettuce",18: "mango",19: "onion",20: "orange",21: "pear",22: "peas",23: "pineapple",24: "pomegranate",25: "potato",26: "radish",27: "spinach",28: "sweetcorn",29: "sweet potato",30: "tomato",31: "turnip",32: "watermelon"}
  indian_foods = {0: 'Datas', 1: 'aloo_gobi', 2: 'aloo_matar', 3: 'aloo_methi', 4: 'aloo_shimla_mirch', 5: 'aloo_tikki', 6: 'anarsa', 7: 'ariselu', 8: 'bandar_laddu', 9: 'basundi', 10: 'bhatura', 11: 'bhindi_masala', 12: 'biryani', 13: 'boondi', 14: 'butter_chicken', 15: 'chak_hao_kheer', 16: 'cham_cham', 17: 'chana_masala', 18: 'chhena_kheeri', 19: 'chicken_razala', 20: 'chicken_tikka', 21: 'chicken_tikka_masala', 22: 'chikki', 23: 'daal_baati_churma', 24: 'daal_puri', 25: 'dal_tadka', 26: 'dharwad_pedha', 27: 'doodhpak', 28: 'double_ka_meetha', 29: 'dum_aloo', 30: 'gajar_ka_halwa', 31: 'gavvalu', 32: 'ghevar', 33: 'gulab_jamun', 34: 'imarti', 35: 'jalebi', 36: 'kachori', 37: 'kadhi_pakoda', 38: 'kajjikaya', 39: 'kakinada_khaja', 40: 'kalakand', 41: 'karela_bharta', 42: 'kofta', 43: 'kuzhi_paniyaram', 44: 'lassi', 45: 'ledikeni', 46: 'litti_chokha', 47: 'lyangcha', 48: 'maach_jhol', 49: 'makki_di_roti_sarson_da_saag', 50: 'malapua', 51: 'misi_roti', 52: 'misti_doi', 53: 'modak', 54: 'mysore_pak', 55: 'naan', 56: 'navrattan_korma', 57: 'palak_paneer', 58: 'paneer_butter_masala', 59: 'phirni', 60: 'pithe', 61: 'poha', 62: 'poornalu', 63: 'pootharekulu', 64: 'qubani_ka_meetha', 65: 'rabri', 66: 'ras_malai', 67: 'rasgulla', 68: 'sandesh', 69: 'shankarpali', 70: 'sheer_korma', 71: 'sheera', 72: 'shrikhand', 73: 'sohan_halwa', 74: 'sohan_papdi', 75: 'sutar_feni', 76: 'unni_appam'}
  output = {"food":None,"type":None,"name":None}

  img  = load_img(path, target_size = (256,256))
  i = img_to_array(img)
  im = preprocess_input(i)
  img = np.expand_dims(im, axis = 0)
  food_or_not_food_pred = np.argmax(food_or_not_food_model.predict(img))
  isfood = ref[food_or_not_food_pred]
  output["food"] = isfood
  if(food_or_not_food_pred == 0):
    healthy_junk_indian_pred = np.argmax(healthy_junk_indian_model.predict(img))
    isTypeFood = ref1[healthy_junk_indian_pred]
    output["type"] = isTypeFood
    if(healthy_junk_indian_pred == 0):
      fruits_vegetables_pred = np.argmax(fruits_vegetables_model.predict(img))
      isFoodName = healthy_foods[fruits_vegetables_pred]
      output["name"] = isFoodName
    elif(healthy_junk_indian_pred == 1):
      indian_foods_pred = np.argmax(indian_foods_model.predict(img))
      output["name"] = indian_foods[indian_foods_pred] 
    elif(healthy_junk_indian_pred == 2):
      junk_food_pred = query(path)
      output["name"] = junk_food_pred
  return output
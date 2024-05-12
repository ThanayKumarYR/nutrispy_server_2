def loading_models():
  from keras.models import load_model
  food_or_not_food_model = load_model("./models/food_or_not_food_classifier.h5")
  healthy_junk_indian_model = load_model("./models/healthy_junk_indian_classifier.h5")
  fruits_vegetables_model = load_model("./models/healthy_fruits_vegetables_classifier.h5")

  return food_or_not_food_model,healthy_junk_indian_model,fruits_vegetables_model

def prediction(path,food_or_not_food_model,healthy_junk_indian_model,fruits_vegetables_model):
  import numpy as np
  from keras.preprocessing.image import img_to_array,load_img
  from keras.applications.mobilenet_v2 import preprocess_input
  from query import query
  ref = {0:"yes", 1: "no"}
  ref1 = {0: 'Healthy Food', 1: 'Indian Food', 2: 'Junk Food'}
  healthy_foods = {0: "apple",1: "banana",2: "beetroot",3: "bell pepper",4: "cabbage",5: "capsicum",6: "carrot",7: "cauliflower",8: "chilli pepper",9: "corn",10: "cucumber",11: "eggplant",12: "garlic",13: "ginger",14: "grapes",15: "kiwi",16: "lemon",17: "lettuce",18: "mango",19: "onion",20: "orange",21: "pear",22: "peas",23: "pineapple",24: "pomegranate",25: "potato",26: "radish",27: "spinach",28: "sweetcorn",29: "sweet potato",30: "tomato",31: "turnip",32: "watermelon"}

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
    elif(healthy_junk_indian_pred == 2):
      junk_food_pred = query(path)
      output["name"] = junk_food_pred
  return output
package cn.piflow.bundle.microorganism.util;


import org.json.JSONArray;
import org.json.JSONObject;

public class BioProject {

    public void convertConcrete2KeyVal(JSONObject parent, String key){ //the object having the key is either a JSONObject, a JSONArray, or a concrete value like string or integer

        if(parent.opt(key) != null){
            Object obj = parent.get(key);

            if(obj instanceof JSONArray){
                for(int i = 0; i < ((JSONArray)obj).length(); i++){
                    Object single = ((JSONArray)obj).get(i);
                    if(isConcrete(single)){
                        JSONObject tmp = new JSONObject();
                        tmp.put("content", single);
                        ((JSONArray) obj).put(i, tmp);
                    }
                }
            }else if(isConcrete(obj)){  //concrete value
                JSONObject tmp = new JSONObject();
                tmp.put("content", obj);
                parent.put(key, tmp);
            }
        }

    }

    public  boolean isConcrete(Object obj){  //any other basic format??
        if(obj instanceof String || obj instanceof Double || obj instanceof Float || obj instanceof Integer || obj instanceof Long){
            return true;
        }else {
            return false;
        }
    }


}
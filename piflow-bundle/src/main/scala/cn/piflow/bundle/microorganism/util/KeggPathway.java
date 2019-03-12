package cn.piflow.bundle.microorganism.util;

import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.regex.Pattern;

public class KeggPathway {

    private static final Pattern sectp = Pattern.compile("^((\\S+)\\s{0,12}(.*)|\\s{2}(\\S+)\\s+(.*))$");
    private static final String END_SEQUENCE_TAG = "///";
    private static final String START_SEQUENCE_TAG = "ENTRY";
    private static boolean hasAnotherSequence = true;


    public static Boolean process(BufferedReader br, JSONObject doc) throws IOException {
        String sectionKey = null;
        String sectionVal = null;
        List section = null;
        List pubmed = new ArrayList();

        do {
            section = ReadSection.readSection(br, sectp, START_SEQUENCE_TAG, END_SEQUENCE_TAG);
            sectionKey = ((String[])section.get(0))[0];
            sectionVal = ((String[])section.get(0))[1];
            if(sectionKey.equals("ENTRY")){
                doc.put("ENTRY", sectionVal.split(" ")[0]);
            }else if(sectionKey.equals("CLASS")){
                doc.put("CLASS",sectionVal);
            }else if(sectionKey.equals("DESCRIPTION")){
                doc.put("DESCRIPTION", sectionVal);
            }else if(sectionKey.equals("NAME")){
                doc.put("NAME", sectionVal);
            }else if(sectionKey.equals("PATHWAY_MAP")){
                doc.put("PATHWAY_MAP", sectionVal);
            }else if(sectionKey.equals("ORGANISM")){
                doc.put("ORGANISM", sectionVal);
            }else if(sectionKey.equals("COMPOUND")){
                doc.put("COMPOUND", sectionVal.replace("\n", ";"));
            }else if(sectionKey.equals("DBLINKS")){
                doc.put("DBLINKS", sectionVal);
            }else if(sectionKey.equals("DISEASE")){
                doc.put("DISEASE", sectionVal.replace("\n", ";"));
            }else if(sectionKey.equals("DRUG")){
                doc.put("DRUG", sectionVal);
            }else if(sectionKey.equals("ENZYME")){
                doc.put("ENZYME", sectionVal.replace("\n", ";"));
            }else if(sectionKey.equals("GENE")){
                doc.put("GENE", sectionVal.replace("\n", ";"));
            }else if (sectionKey.equals("MODULE")){
                doc.put("MODULE",sectionVal.replace("\n", ";"));
            }else if(sectionKey.equals("ORTHOLOGY")){
                doc.put("ORTHOLOGY", sectionVal.replace("\n", ";"));
            }else if(sectionKey.equals("KO_PATHWAY")){
                doc.put("KO_PATHWAY", sectionVal);
            }else if(sectionKey.equals("REACTION")){
                doc.put("REACTION",sectionVal.replace("\n", ";"));
            }else if(sectionKey.equals("REFERENCE")){
                if(sectionVal.indexOf("PMID") != -1){
                    pubmed.add(sectionVal.substring(6));
                    doc.put("PUBMED", pubmed);
                }
            }
        }while(!sectionKey.equals(END_SEQUENCE_TAG));


        while (true){
            br.mark(1);
            int c = br.read();
            if (c == -1) {
                hasAnotherSequence = false;
                break;
            }
            if (Character.isWhitespace((char) c)) {
                //hasInternalWhitespace = true;
                continue;
            }
            br.reset();
            break;
        }
        return hasAnotherSequence;
    }
}

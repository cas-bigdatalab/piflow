package cn.piflow.bundle.microorganism.util;


import org.biojava.bio.seq.io.ParseException;
import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;


public class Pfam {

    //Compulsory fields
    protected static final String IDENTIFICATION_TAG = "ID";
    protected static final String ACCESSION_TAG = "AC";
    protected static final String DEFINITION_TAG = "DE";
    protected static final String AUTHOR_TAG = "AU";
    protected static final String SEED_SOURCE_TAG = "SE";
    protected static final String STRUCTURE_SOURCE_TAG = "SS";
    protected static final String BUILD_METHOD_TAG = "BM";
    protected static final String SEARCH_METHOD_TAG = "SM";
    protected static final String GATHERING_THRESHOLD_TAG = "GA";
    protected static final String TRUSTED_CUTOFF_TAG = "TC";
    protected static final String NOISE_CUTOFF_TAG = "NC";
    protected static final String TYPE_TAG = "TP";
    protected static final String SEQUENCE_TAG = "SQ";
    //Optional fields
    protected static final String DATABASE_COMMENT_TAG = "DC";
    protected static final String DATABASE_REFERENCE_TAG = "DR";
    protected static final String REF_COMMENT_TAG = "RC";
    protected static final String REF_NUMBER_TAG = "RN";
    protected static final String REF_MEDLINE_TAG = "RM";
    protected static final String REF_TITLE_TAG = "RT";
    protected static final String REF_AUTHOR_TAG = "RA";
    protected static final String REF_LOCATION_TAG = "RL";
    protected static final String PRE_IDENTIFIER_TAG = "PI";
    protected static final String KEYWORDS_TAG = "KW";
    protected static final String COMMENT_TAG = "CC";
    protected static final String PFAM_ACCESSION_TAG = "NE";  //INDICATES A NESTED DOMAIN
    protected static final String LOCATION_TAG = "NL";  //location of nested domain-sequence ID,start and end of insert
    protected static final String WIKI_LINK_TAG = "WK";
    protected static final String CLAN_TAG = "CL";    //clan accession
    protected static final String MEMBERSHIP_TAG = "MB";

    protected static final String END_SEQUENCE_TAG = "//";

    protected static final String STOCKHOLM_TAG = "# STOCKHOLM 1.0";

    protected static final Pattern gsseqp = Pattern.compile("^(.+)/(\\d+)-(\\d+)\\s+([A-Z]{2})\\s+(.+)$");
    protected static final Pattern seqp = Pattern.compile("^(\\S+)/(\\d+-\\d+)\\s+(.+)$");
    protected static final Pattern gcp = Pattern.compile("^(\\S+)\\s+(.+)$");

    private static boolean hasAnotherSequence = true;

    public static boolean process(BufferedReader br, JSONObject doc) throws IOException {
        String sectionKey = null;
        String sectionVal = null;
        JSONArray dbRefs = new JSONArray();
        JSONArray gcLines = new JSONArray();
        JSONArray rankedRefs = new JSONArray();
        Map<String, JSONObject> sequences = new HashMap<String, JSONObject>();
        try {
            List section = null;
            do{
                section = readSection(br);
                sectionKey = ((String[]) section.get(0))[0];
                sectionVal = ((String[]) section.get(0))[1];
                if(section.size() == 1 && sectionVal != null){
                    sectionVal = sectionVal.trim();
                    if(sectionVal.contains("\n")){
                        sectionVal = sectionVal.replaceAll("\\n", "");
                    }
                    if(sectionVal.endsWith(";")) sectionVal = sectionVal.substring(0, sectionVal.length()-1);

                    if(sectionKey.equals(IDENTIFICATION_TAG)){
                        doc.put("identification", sectionVal);
                    }else if(sectionKey.equals(ACCESSION_TAG)){
                        doc.put("accession", sectionVal);
                    }else if(sectionKey.equals(DEFINITION_TAG)){
                        doc.put("definition", sectionVal);
                    }else if(sectionKey.equals(AUTHOR_TAG)){
                        doc.put("author", sectionVal);
                    }else if(sectionKey.equals(GATHERING_THRESHOLD_TAG)){
                        doc.put("gathering_threshold", sectionVal);
                    }else if(sectionKey.equals(TRUSTED_CUTOFF_TAG)){
                        doc.put("trusted_cutoff", sectionVal);
                    }else if(sectionKey.equals(NOISE_CUTOFF_TAG)){
                        doc.put("noise_cutoff", sectionVal);
                    }else if(sectionKey.equals(TYPE_TAG)){
                        doc.put("type", sectionVal);
                    }else if(sectionKey.equals(SEQUENCE_TAG)){
                        doc.put("sequence_length", Integer.parseInt(sectionVal));
                    }else if(sectionKey.equals(SEED_SOURCE_TAG)){
                        doc.put("seed_source", sectionVal);
                    }else if(sectionKey.equals(STRUCTURE_SOURCE_TAG)){
                        doc.put("struc_source", sectionVal);
                    }else if(sectionKey.equals(BUILD_METHOD_TAG)){
                        doc.put("build_method", sectionVal);
                    }else if(sectionKey.equals(SEARCH_METHOD_TAG)){
                        doc.put("search_method", sectionVal);
                    }else if(sectionKey.equals(PRE_IDENTIFIER_TAG)){
                        doc.put("pre_identifier", sectionVal);
                    }else if(sectionKey.equals(KEYWORDS_TAG)){
                        doc.put("keywords", sectionVal);
                    }else if(sectionKey.equals(COMMENT_TAG)){
                        doc.put("comment", sectionVal);
                    }else if(sectionKey.equals(PFAM_ACCESSION_TAG)){
                        doc.put("pfam_accession", sectionVal);
                    }else if(sectionKey.equals(LOCATION_TAG)){
                        doc.put("location", sectionVal);
                    }else if(sectionKey.equals(WIKI_LINK_TAG)){
                        doc.put("wiki_link", sectionVal);
                    }else if(sectionKey.equals(CLAN_TAG)){
                        doc.put("clan", sectionVal);
                    }else if(sectionKey.equals(MEMBERSHIP_TAG)){
                        doc.put("membership", sectionVal);
                    }else if(sectionKey.equals(DATABASE_REFERENCE_TAG)){
                        JSONObject dbRef = new JSONObject();
                        String[] parts = sectionVal.split(";");
                        dbRef.put("databaseName", parts[0].trim());
                        dbRef.put("databaseID", parts[1].trim());
                        dbRefs.put(dbRef);
                    }else if(sectionKey.equals("STOCKHOLM")){
                        //do nothing
                    }else if(sectionKey.equals("GSMarkUp")){
                        JSONObject seq = new JSONObject();
                        Matcher m = gsseqp.matcher(sectionVal);
                        if(m.matches()){
                            String seq_name = m.group(1);
                            String seq_start = m.group(2);
                            String seq_end = m.group(3);
                            String feature_tag = m.group(4);
                            String feature_value = m.group(5);
                            seq.put("seq_name", seq_name);
                            seq.put("seq_start",seq_start);
                            seq.put("seq_end", seq_end);
                            seq.put(feature_tag, feature_value);
                            sequences.put(seq_name, seq);
                        }
                    }else if(sectionKey.equals("Sequence")){  // sequence line with no previous tag
                        Matcher m = seqp.matcher(sectionVal);
                        if(m.matches()){
                            String seq_name = m.group(1);
                            String sequence = m.group(3);
                            if(sequences.containsKey(seq_name)){
                                sequences.get(seq_name).put("sequence", sequence);
                            }
                        }
                    }else if(sectionKey.equals("GRMarkUp")){  // more info just below the sequence
                        Matcher m = gsseqp.matcher(sectionVal);
                        if(m.matches()){
                            String seq_name = m.group(1);
                            String feature_tag = m.group(4);
                            String feature_val = m.group(5);
                            if(sequences.containsKey(seq_name)){
                                sequences.get(seq_name).put(feature_tag, feature_val);
                            }
                        }
                    }else if(sectionKey.equals("GCMarkUp")){
                        Matcher m = gcp.matcher(sectionVal);
                        if(m.matches()){
                            JSONObject gcObj = new JSONObject();
                            String feature_tag = m.group(1);
                            String feature_val = m.group(2);
                            gcObj.put(feature_tag, feature_val);
                            gcLines.put(gcObj);
                        }
                    }else{
                        String name = sectionKey.toLowerCase();
                        doc.put(name, sectionVal);
                    }
                } else if(section.size() > 1){
                    sectionKey = ((String[]) section.get(0))[0];
                    if(sectionKey.equals(REF_NUMBER_TAG)){   // this section is a reference
                        JSONObject refObj = new JSONObject();
                        String refRank = sectionVal.trim();
                        refRank = refRank.substring(1, refRank.length()-1);
                        int ref_rank = Integer.parseInt(refRank);
                        String medlineID = null;
                        String title = null;
                        String authors = null;
                        String location = null;
                        String comment = null;
                        for(int i = 1; i < section.size(); i++){
                            String key = ((String[])section.get(i))[0];
                            String val = ((String[])section.get(i))[1].trim();
                            if(val.contains("\n")){
                                val = val.replaceAll("\\n", "");
                            }
                            if (val.endsWith(";")) val = val.substring(0, val.length()-1);
                            if(key.equals(REF_MEDLINE_TAG)){medlineID = val;}
                            if(key.equals(REF_TITLE_TAG)){title = val;}
                            if(key.equals(REF_AUTHOR_TAG)){authors = val;}
                            if(key.equals(REF_LOCATION_TAG)){location = val;}
                            if(key.equals(REF_COMMENT_TAG)){
                                comment = val;
                            }
                        }
                        refObj.put("rank", ref_rank);
                        refObj.put("medlineID", Integer.parseInt(medlineID));
                        refObj.put("title", title);
                        refObj.put("authors", authors);
                        refObj.put("location", location);
                        refObj.put("comment", comment);
                        rankedRefs.put(refObj);
                    }else if(sectionKey.equals(DATABASE_REFERENCE_TAG)){
                        JSONObject dbRef = new JSONObject();
                        String[] parts = sectionVal.split(";");
                        dbRef.put("databaseName", parts[0].trim());
                        dbRef.put("databaseID", parts[1].trim());

                        StringBuffer comment = new StringBuffer();
                        for(int i = 1; i < section.size(); i++){
                            String key = ((String[])section.get(i))[0];
                            String val = ((String[])section.get(i))[1].trim();
                            if(key.equals(DATABASE_COMMENT_TAG)){
                                comment.append(val);
                            }
                        }
                        dbRef.put("comment", comment.toString());
                        dbRefs.put(dbRef);
                    }
                }
            }while (!sectionKey.equals(END_SEQUENCE_TAG));
            doc.put("dbRefs", dbRefs);
            doc.put("gcLines", gcLines);
            JSONArray sequencesArr = new JSONArray();
            for(Map.Entry<String, JSONObject> entry : sequences.entrySet()){
                sequencesArr.put(entry.getValue());
            }
            // TODO: 2016/6/24 solve the outofmemory error as the sequences are too large, and we keep two copy right now. when put to doc, would get 3 copy.
            doc.put("sequences", sequencesArr);
            doc.put("rankedRefs", rankedRefs);
        }  catch (ParseException e) {
            e.printStackTrace();
        }

        while (true){
            br.mark(1);
            int c = br.read();
            if (c == -1) {
                hasAnotherSequence = false;
                break;
            }
            if (Character.isWhitespace((char) c)) {
                continue;
            }
            br.reset();
            break;
        }
        return hasAnotherSequence;
    }

    public static List readSection(BufferedReader br) throws ParseException {
        List section = new ArrayList();
        String line;
        boolean done = false;

        try {
            while (!done) {
                br.mark(160);
                line = br.readLine();

                if(line.equals(STOCKHOLM_TAG)){
                    done = true;
                    section.add(new String[]{"STOCKHOLM", null});
                }else if(line.startsWith("#=GF")){
                    String token = line.substring(5,7);
                    if(token.equals(DEFINITION_TAG)){
                        section.add(new String[]{DEFINITION_TAG, line.substring(8)});
                        done = true;
                    }else if(token.charAt(0) == 'R' || token.charAt(0) == 'D'){
                        br.reset();
                        String currentTag = null;
                        char currentTagStart = '\0';
                        StringBuffer currentVal = null;

                        while(!done){
                            br.mark(160);
                            line = br.readLine();

                            if (currentTagStart=='\0') currentTagStart = line.charAt(5);
                            if (!line.startsWith("#=GF "+currentTagStart) ||
                                    (currentTagStart=='R' && currentTag!=null && line.substring(5,7).equals(REF_NUMBER_TAG)) ||
                                    (currentTagStart=='D' && currentTag!=null && line.substring(5,7).equals(DATABASE_REFERENCE_TAG))) {
                                br.reset();
                                done = true;
                                // dump current tag if exists
                                if (currentTag!=null) section.add(new String[]{currentTag,currentVal.toString()});
                            } else {
                                try {
                                    String tag = line.substring(5, 7);
                                    String value = line.substring(8);
                                    if (currentTag==null || !tag.equals(currentTag)) {
                                        if (currentTag!=null) section.add(new String[]{currentTag,currentVal.toString()});
                                        currentTag = tag;
                                        currentVal = new StringBuffer();
                                        currentVal.append(value);
                                    } else {
                                        currentVal.append("\n");
                                        currentVal.append(value);
                                    }
                                } catch (Exception e) {
                                    throw new ParseException(e);
                                }
                            }
                        }
                    }else {  //values in multiple lines or single line
                        StringBuffer currentVal = new StringBuffer();
                        currentVal.append(line.substring(8).trim());
                        while (!done) {
                            br.mark(160);
                            line = br.readLine();
                            if(!line.substring(5,7).equals(token) || !line.startsWith("#=GF")){  // the following  #=GS line might have "SQ" in the right position
                                br.reset();
                                done = true;
                                section.add(new String[]{token,currentVal.toString()});
                            }else{
                                currentVal.append("\n");
                                currentVal.append(line.substring(8).trim());
                            }
                        }
                    }
                } else if(line.startsWith("#=GS")){
                    done = true;
                    section.add(new String[]{"GSMarkUp", line.substring(5).trim()});
                } else if(line.startsWith("#=GR")){
                    done = true;
                    section.add(new String[]{"GRMarkUp", line.substring(5).trim()});
                } else if(line.startsWith("#=GC")){
                    done = true;
                    section.add(new String[]{"GCMarkUp", line.substring(5).trim()});
                } else if(line.startsWith(END_SEQUENCE_TAG)){
                    section.add(new String[]{END_SEQUENCE_TAG,null});
                    done = true;
                } else{  //no prefix tag
                    done = true;
                    section.add(new String[]{"Sequence", line.trim()});
                }
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
        return section;
    }
}

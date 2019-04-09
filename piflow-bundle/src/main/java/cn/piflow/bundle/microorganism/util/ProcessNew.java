package cn.piflow.bundle.microorganism.util;



import org.biojava.bio.seq.Feature;
import org.biojavax.*;
import org.biojavax.bio.seq.RichFeature;
import org.biojavax.bio.seq.RichSequence;
import org.biojavax.ontology.SimpleComparableTerm;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Created by xiujuan on 2016/3/24.
 */
public class ProcessNew {

    static final Logger logger = LoggerFactory.getLogger(ProcessNew.class);
    static final Pattern dp = Pattern.compile("(\\d{4})");
    static final Pattern llp = Pattern.compile("(\\S+)\\s([SN])\\s(\\S+)\\s([WE])");
    static final Pattern submitDatep = Pattern.compile("^Submitted\\s+\\((\\S+)\\)\\s+(.*)$");
    static final SimpleDateFormat formatter = new SimpleDateFormat("yyyy-MM-dd");
    static final SimpleDateFormat format = new SimpleDateFormat("dd-MMM-yyyy", Locale.ENGLISH);

    // static AddressCountryDict dict = AddressCountryDict.getInstance();

    public static HashMap<String,Object> processSingleSequence(RichSequence seq) throws ParseException {
        //try{
        // logger.info("doc: " + seq.getAccession());

        HashMap<String,Object> map = new HashMap() ;


        map.put("Sequence", seq.seqString());
        map.put("Accession", seq.getAccession());

        map.put("SequenceLength", seq.getInternalSymbolList().length());
        if (seq.getTaxon() != null) {
            map.put("TaxonID", seq.getTaxon().getNCBITaxID());
            map.put("Organism", seq.getTaxon().getDisplayName());
        }
        map.put("Description", seq.getDescription().replace('\n', ' '));

        map.put("Division", seq.getDivision());
        map.put("Identifier", seq.getIdentifier());
        map.put("Version", seq.getVersion());

        if (seq.getCircular()) {
            map.put("Topology", "Circular");
        } else {
            map.put("Topology", "Linear");
        }


        for (Note note : seq.getNoteSet()) {
            String noteName = note.getTerm().toString().substring(9);
            if (noteName.indexOf("moltype") != -1) {
                map.put("MoleculeType", note.getValue());
            } else if (noteName.indexOf("Organism") != -1) {
                String organism = note.getValue();
                //doc.put("Organism", organism.substring(0,organism.indexOf("\n")));
                map.put("Lineage", organism.substring(organism.indexOf("\n")).replaceAll("\n", ""));
            } else if (noteName.indexOf("acc") != -1) {
                map.put("AdditionalAccs", note.getValue());
            } else if (noteName.indexOf("DBLink") != -1) {   //deal with dblinks
                JSONArray dbLinks = new JSONArray();
                String[] val = note.getValue().split("\\n");
                for (String v : val) {
                    int index = v.indexOf(":");
                    if (index != -1) {
                        JSONObject link = new JSONObject();
                        link.put(v.substring(0, index), v.substring(index + 1).trim());
                        dbLinks.put(link);
                    } else {  // value splitted into more than one line
                        JSONObject last = dbLinks.getJSONObject(dbLinks.length() - 1);
                        String key = last.keys().next();
                        String value = last.get(key).toString();
                        String newVal = value + v;
                        last.put(key, newVal);
                    }
                }
                map.put("dbLinks", dbLinks);
            } else if (noteName.equals("kw")) {
                map.put("KeyWords", note.getValue());
            } else if (noteName.equals("udat")) {
                map.put("dateUpdated", formatter.format(format.parse(note.getValue())));
            } else {
                map.put(noteName, note.getValue());
            }
        }

        //features
        JSONArray featureArray = new JSONArray();
        Iterator<Feature> featureIterator = seq.features();
        List<String> isolates = new ArrayList<String>();
        while (featureIterator.hasNext()) {
            JSONObject featureObject = new JSONObject();
            List<String> dbxrefArray = new ArrayList<String>();
            RichFeature feature = (RichFeature) featureIterator.next();
            for (RankedCrossRef rankedCrossRef : feature.getRankedCrossRefs()) {
                dbxrefArray.add(rankedCrossRef.getCrossRef().getDbname() + ":" + rankedCrossRef.getCrossRef().getAccession());
            }
            featureObject.put("db_xref", dbxrefArray);

            featureObject.put("featureType", feature.getType());
            Map featureMap = feature.getAnnotation().asMap();
            Iterator<SimpleComparableTerm> featureKeyIterator = featureMap.keySet().iterator();
            while (featureKeyIterator.hasNext()) {
                SimpleComparableTerm term = featureKeyIterator.next();
                String name = term.getName();
                String nameValue = featureMap.get(term).toString();
                //isolate is an array?

                if (name.indexOf("altitude") != -1) {
                    featureObject.put("altitude_value", Float.valueOf(nameValue.substring(0, nameValue.indexOf(" "))));  //number, take care of negative number
                } else if (name.indexOf("collection_date") != -1) {
                    if (getCollectionYear(nameValue) != 0) {
                        featureObject.put("collection_year", getCollectionYear(nameValue));
                    }
                } else if (name.indexOf("country") != -1) {
                    if (nameValue.indexOf(":") != -1) {
                        featureObject.put("CollectionCountry", nameValue.substring(0, nameValue.indexOf(":")));
                    }
                } else if (name.indexOf("culture_collection") != -1) {
                    int index = nameValue.indexOf(":") != -1 ? nameValue.indexOf(":") : nameValue.indexOf(" ");
                    if (index != -1) {
                        featureObject.put("InstitutionCode", nameValue.substring(0, index));
                        featureObject.put("CultureID", nameValue.substring(index + 1));
                    }
                } else if (name.indexOf("lat_lon") != -1) {
                    Float[] arr = getLat_Lon(nameValue);
                    if (arr != null) {
                        featureObject.put("Latitude", arr[0]);
                        featureObject.put("Longitude", arr[1]);
                    }
                } else if (name.indexOf("pathovar") != -1) {

                } else if (feature.getType().equals("source") && name.equals("isolate")) {
                    isolates.add(nameValue);
                }
                featureObject.put(term.getName(), featureMap.get(term));
            }
            featureArray.put(featureObject);
            //for garbage collection
            featureObject = null;
            dbxrefArray = null;
            feature = null;
            featureMap = null;
        }
        map.put("features", featureArray);
        if (isolates.size() > 0) {
            map.put("isolate_all", isolates);
        }
        return map;
    }

    public static int getCollectionYear(String date){
        Matcher m = dp.matcher(date);
        String year;
        if(m.find()){
            year = m.group(1);
            return Integer.parseInt(year);
        }else{
            return 0;
        }
    }

    public static Float[] getLat_Lon(String lat_lon){
        Matcher m = llp.matcher(lat_lon);
        Float[] array = null;
        try{
            if(m.matches()){
                array = new Float[2];
                if(m.group(2).equals("N")){
                    array[0] = Float.valueOf(m.group(1));
                }else{
                    array[0] = Float.valueOf("0")-Float.valueOf(m.group(1));
                }
                if(m.group(4).equals("E")){
                    array[1] = Float.valueOf(m.group(3));
                }else{
                    array[1] = Float.valueOf("0")-Float.valueOf(m.group(3));
                }
            }
        }catch (NumberFormatException nfe){
            return null;
        }
        return array;
    }

    public static void processUniprotSeq(RichSequence seq, JSONObject doc) throws ParseException {
        logger.info("doc: " + seq.getAccession());
        doc.put("Accession", seq.getAccession());
        doc.put("Name", seq.getName());
        doc.put("Division", seq.getDivision());
        doc.put("Description", seq.getDescription().replace('\n', ' '));
        doc.put("Version", seq.getVersion());
        doc.put("sequencelength", seq.length());
        //Taxon
        doc.put("TaxonID", seq.getTaxon().getNCBITaxID());
        for(Object name: seq.getTaxon().getNameClasses()){
            doc.put("Taxon_"+(String)name, seq.getTaxon().getNames((String)name));
        }

        //rankedcrossrefs
        /*JSONArray rankedCrossRefs = new JSONArray();
        for(RankedCrossRef rankedCrossRef : seq.getRankedCrossRefs()){
            JSONObject ref = new JSONObject();
            String key = rankedCrossRef.getCrossRef().getDbname();
            String accessions = rankedCrossRef.getCrossRef().getAccession();
            for(Note note : rankedCrossRef.getCrossRef().getRichAnnotation().getNoteSet()){
                accessions += ";"+note.getValue();
            }
            ref.put(key, accessions);
            rankedCrossRefs.put(ref);
        }
        if(rankedCrossRefs.length() > 0){
            doc.put("rankedCrossRefs", rankedCrossRefs);
        }*/
        processRankedCrossRefs(seq, doc);
        //comments
        JSONArray comments = new JSONArray();
        for(Comment comment : seq.getComments()){
            JSONObject cmtObj = new JSONObject();
            String cmt = comment.getComment().replace('\n', ' ');
            cmt = cmt.substring(3);
            int index = cmt.indexOf(":");
            cmtObj.put(cmt.substring(0,index).trim(),cmt.substring(index+1).trim());
            comments.put(cmtObj);
        }
        if(comments.length() > 0){
            doc.put("comments", comments);
        }
        //features
        JSONArray features = new JSONArray();
        Iterator<Feature> featureIterator = seq.features();
        while(featureIterator.hasNext()){
            JSONObject featureObject = new JSONObject();
            List<String> dbxrefArray = new ArrayList<String>();
            RichFeature feature = (RichFeature)featureIterator.next();
            for(RankedCrossRef rankedCrossRef : feature.getRankedCrossRefs()){
                dbxrefArray.add(rankedCrossRef.getCrossRef().getDbname() + ":" + rankedCrossRef.getCrossRef().getAccession());
            }
            if(dbxrefArray.size() > 0){
                featureObject.put("rankedCrossRefs", dbxrefArray);
            }
            featureObject.put("type", feature.getType());
            featureObject.put("location_start", feature.getLocation().getMin());
            featureObject.put("location_end", feature.getLocation().getMax());
            Map featureMap = feature.getAnnotation().asMap();
            Iterator<SimpleComparableTerm> featureKeyIterator = featureMap.keySet().iterator();
            while(featureKeyIterator.hasNext()){
                SimpleComparableTerm term = featureKeyIterator.next();
                featureObject.put(term.getName(),featureMap.get(term));
            }
            features.put(featureObject);
        }
        if(features.length() > 0){
            doc.put("features", features);
        }
        //sequence
        doc.put("sequence", seq.seqString());

        JSONArray rankedDocRefs = new JSONArray();
        Map<Integer,List<String>> rankedDocRefs_addiInfo = new HashMap<Integer, List<String>>();
        //properties from notes: rlistener.addSequenceProperty
        List<String> keywords = new ArrayList<String>();
        List<String> secondaryAccs = new ArrayList<String>();
        JSONArray organismHosts = new JSONArray();
        for(Note note : seq.getNoteSet()){
            String note_term = note.getTerm().getName();
            if(note_term.equals("kw")){
                keywords.add(note.getValue());
            }else if(note_term.equals("cdat")){
                doc.put("dateCreated", formatter.format(format.parse(note.getValue())));
            }else if(note_term.equals("udat")){
                doc.put("dateUpdated", formatter.format(format.parse(note.getValue())));
            }else if(note_term.equals("adat")){
                doc.put("dateAnnotated", formatter.format(format.parse(note.getValue())));
            }else if(note_term.equals("arel")){
                doc.put("relAnnotated", note.getValue());
            }else if(note_term.equals("Organism host")){
                JSONObject organismHost = new JSONObject();
                String sciname;
                String comname;
                String names = null;
                List synonym = new ArrayList();
                String[] parts = note.getValue().split(";");
                if(parts[0].matches("\\S+=\\S+")){
                    String[] moreparts = parts[0].split("=");
                    if(moreparts[0].equals("NCBI_TaxID")){
                        organismHost.put("NCBI_TaxID",Integer.parseInt(moreparts[1]));
                    }else{
                        organismHost.put(moreparts[0],moreparts[1]);
                    }
                }else{
                    names = parts[0];
                }
                if(parts.length > 1){
                    names = parts[1];
                }
                if(names != null){
                    if (names.endsWith(".")) names = names.substring(0,names.length()-1); // chomp trailing dot
                    String[] nameparts = names.split("\\(");
                    sciname = nameparts[0].trim();
                    organismHost.put("scientific name", sciname);
                    if (nameparts.length>1) {
                        comname = nameparts[1].trim();
                        if (comname.endsWith(")")) comname = comname.substring(0,comname.length()-1); // chomp trailing bracket
                        organismHost.put("common name", comname);
                        if (nameparts.length>2) {
                            // synonyms
                            for (int j = 2 ; j < nameparts.length; j++) {
                                String syn = nameparts[j].trim();
                                if (syn.endsWith(")")) syn = syn.substring(0,syn.length()-1); // chomp trailing bracket
                                synonym.add(syn);
                            }
                            organismHost.put("synonym", synonym);
                        }
                    }
                }
                organismHosts.put(organismHost);
            }else if(note_term.equals("Sequence meta info")){
                String seqMetaInfo = note.getValue();
                if(seqMetaInfo.startsWith("SEQUENCE")){
                    seqMetaInfo = seqMetaInfo.substring(8);
                }
                String[] parts = seqMetaInfo.split(";");
                if(parts.length > 1){
                    doc.put("molecular weight", Integer.parseInt(parts[1].trim().split(" ")[0]));
                    if(parts.length > 2){
                        String[] moreparts = parts[2].trim().split(" ");
                        doc.put(moreparts[1], moreparts[0]);
                    }
                }
            }else if(note_term.startsWith("docref")){
                int rank = Integer.parseInt(note.getValue().split(":")[0].trim());
                String key = note_term.substring(7);  //remove the precedding "docref_"
                if(key.contains("biojavax:")){
                    key = key.substring(9);   //remove "biojavax:"
                }
                String value = note.getValue().substring(note.getValue().indexOf(":")+1).trim();
                if(rankedDocRefs_addiInfo.containsKey(rank)){
                    rankedDocRefs_addiInfo.get(rank).add(key+":"+value);
                }else{
                    List<String> tmp = new ArrayList<String>();
                    tmp.add( key+":"+value);
                    rankedDocRefs_addiInfo.put(rank,tmp);
                }
            }else if(note_term.equals("acc")){
                secondaryAccs.add(note.getValue());
            }else{
                doc.put(note_term, note.getValue());
            }
        }
        if(secondaryAccs.size() > 0){
            doc.put("secondaryacc",secondaryAccs);
        }
        if(organismHosts.length() > 0){
            doc.put("organismhost", organismHosts);
        }
        if(keywords.size() > 0){
            doc.put("keywords", keywords);
        }

        //rankeddocref
        for(RankedDocRef rankedDocRef : seq.getRankedDocRefs()){
            JSONObject rankedDocRefObj = new JSONObject();
            DocRef docRef = rankedDocRef.getDocumentReference();
            rankedDocRefObj.put("rank", rankedDocRef.getRank());
            rankedDocRefObj.put("authors", docRef.getAuthors());
            rankedDocRefObj.put("title", docRef.getTitle());
            rankedDocRefObj.put("location", docRef.getLocation());
            rankedDocRefObj.put("remark", docRef.getRemark());
            for(Map.Entry entry : rankedDocRefs_addiInfo.entrySet()){
                if((Integer)(entry.getKey()) == rankedDocRef.getRank()){
                    for(String pair : (List<String>)(entry.getValue())){
                        int index = pair.indexOf(":");
                        rankedDocRefObj.put(pair.substring(0, index),pair.substring(index+1));
                    }
                }
            }
            rankedDocRefs.put(rankedDocRefObj);
        }
        if(rankedDocRefs.length() > 0){
            doc.put("rankedDocRefs", rankedDocRefs);
        }
    }

    public static void processEMBL_EnsemblSeq(RichSequence seq,JSONObject doc) throws ParseException {
        logger.info("accession: " + seq.getName());
        if(seq.getCircular()){
            doc.put("Topology", "Circular");
        }else{
            doc.put("Topology", "Linear");
        }
        for(Note note : seq.getNoteSet()){
            String noteName = note.getTerm().toString().substring(9);
            if(noteName.equals("moltype")){
                doc.put("Molecule type", note.getValue());
            }else if(noteName.equals("organism")){
                doc.put("Classfication", note.getValue().replaceAll("\n", ""));
            }else if(noteName.equals("kw")){
                doc.put("KeyWords", note.getValue());
            }else if(noteName.equals("udat")){
                doc.put("dateUpdated", formatter.format(format.parse(note.getValue())));
            }else if(noteName.equals("cdat")){
                doc.put("dateCreated", formatter.format(format.parse(note.getValue())));
            }else{
                doc.put(noteName, note.getValue());
            }
        }
        doc.put("SequenceLength", seq.getInternalSymbolList().length());
        doc.put("Description", seq.getDescription().replace('\n', ' '));
        //System.out.println(seq.getInternalSymbolList().length());
        //doc.put("Sequence length", seq.getInternalSymbolList().length());
        doc.put("Accession", seq.getName());
        doc.put("Organism",seq.getTaxon().getDisplayName());
        doc.put("TaxonID", seq.getTaxon().getNCBITaxID());

        /*for (RankedDocRef rankDocRef : seq.getRankedDocRefs()){
            if(rankDocRef.getDocumentReference().getLocation().indexOf("Submitted") != -1){
                int dotindex = rankDocRef.getDocumentReference().getLocation().indexOf(".");
                String submitDate = rankDocRef.getDocumentReference().getLocation().substring(11,22);
                String submitAddress = rankDocRef.getDocumentReference().getLocation().substring(dotindex+1).trim();
                doc.put("SubmitDate", format.parse(submitDate));
                doc.put("SubmittedAddress", rankDocRef.getDocumentReference().getLocation().substring(dotindex+1).trim());
            }
        }*/
        //rankedDocRefs
        //processRankedDocRefs(seq, doc);

        //rankedCrossRef
        processRankedCrossRefs(seq, doc);

        //comments
        processComment(seq, doc);

        //features
        JSONArray featureArray = new JSONArray();
        Iterator<Feature> featureIterator = seq.features();
        while (featureIterator.hasNext()){
            JSONObject featureObject = new JSONObject();
            List<String> dbxrefArray = new ArrayList<String>();
            RichFeature feature = (RichFeature)featureIterator.next();
            //deal with db_xref in each feature
            //db_xref is not required in the requirement
            for(RankedCrossRef rankedCrossRef : feature.getRankedCrossRefs()){
                dbxrefArray.add(rankedCrossRef.getCrossRef().getDbname() + ":" + rankedCrossRef.getCrossRef().getAccession());
            }
            featureObject.put("db_xref", dbxrefArray);

            featureObject.put("featureType", feature.getType());
            Map featureMap = feature.getAnnotation().asMap();
            Iterator<SimpleComparableTerm> featureKeyIterator = featureMap.keySet().iterator();
            while(featureKeyIterator.hasNext()){
                SimpleComparableTerm term = featureKeyIterator.next();
                String name = term.getName();
                String nameValue = featureMap.get(term).toString();

                if(name.equals("altitude")){
                    featureObject.put("altitude_value", Float.valueOf(nameValue.substring(0,nameValue.indexOf("m")).trim()));  //number, take care of negative number
                }else if(name.equals("collection_date")){
                    JSONArray collectionDates = new JSONArray();
                    for(String singleDate : nameValue.split("/")){
                        JSONObject collectionDate = new JSONObject();
                        if(singleDate.endsWith("FT")){
                            singleDate = singleDate.substring(0, singleDate.length()-2);
                        }
                        if(singleDate.matches("\\d{2}-\\w{3}-\\d{4}")){
                            collectionDate.put("collection_date", formatter.format(format.parse(singleDate)));
                        }else{
                            collectionDate.put("collection_date", singleDate);
                        }

                        collectionDate.put("collection_year", getCollectionYear(singleDate));
                        collectionDates.put(collectionDate);
                    }
                    featureObject.put("collectionDate", collectionDates);
                }
                featureObject.put(term.getName(),featureMap.get(term));
            }
            featureArray.put(featureObject);
        }
        doc.put("features", featureArray);
    }

    public static void processRankedCrossRefs(RichSequence seq, JSONObject doc){
        JSONArray rankedCrossRefs = new JSONArray();
        for(RankedCrossRef rankedCrossRef : seq.getRankedCrossRefs()){
            JSONObject ref = new JSONObject();
            String key = rankedCrossRef.getCrossRef().getDbname();
            String accessions = rankedCrossRef.getCrossRef().getAccession();
            for(Note note : rankedCrossRef.getCrossRef().getRichAnnotation().getNoteSet()){
                accessions += ";"+note.getValue();
            }
            ref.put(key, accessions);
            rankedCrossRefs.put(ref);
        }
        if(rankedCrossRefs.length() > 0){
            doc.put("rankedCrossRefs", rankedCrossRefs);
        }
    }

//    public static void processRankedDocRefs(RichSequence seq, JSONObject doc) throws ParseException {
//        JSONArray rankedDocRefs = new JSONArray();
//        for(RankedDocRef rankedDocRef : seq.getRankedDocRefs()){
//            DocRef docRef = rankedDocRef.getDocumentReference();
//            JSONObject rankedRef = new JSONObject();
//            rankedRef.put("authors", docRef.getAuthors());
//            rankedRef.put("title", docRef.getTitle());
//            if(docRef.getCrossref() != null){
//                String dbName = docRef.getCrossref().getDbname();
//                if(dbName.equals("PUBMED")){
//                    rankedRef.put(dbName, Integer.parseInt(docRef.getCrossref().getAccession()));
//                }else{
//                    rankedRef.put(dbName, docRef.getCrossref().getAccession());
//                }
//            }
//            Matcher m = submitDatep.matcher(docRef.getLocation().replaceAll("\n", " "));
//            if(m.matches()){
//                rankedRef.put("SubmitDate", formatter.format(format.parse(m.group(1))));
//                rankedRef.put("SubmitAddress", m.group(2));
//                int year = Integer.parseInt(m.group(1).substring(m.group(1).lastIndexOf("-")+1));
//                rankedRef.put("SubmitYear", year);
//                //submitCountry--extract from SubmitAddress
//                String countryName = dict.mappingCountry(m.group(2));
//                if(countryName != null){
//                    rankedRef.put("SubmitCountry", countryName);
//                }
//            }
//            rankedDocRefs.put(rankedRef);
//        }
//        doc.put("rankedDocRefs", rankedDocRefs);
//    }

    public static void processComment(RichSequence seq, JSONObject doc){
        Map<String, String> commentMetaData = new HashMap<String, String>();
        JSONArray comments = new JSONArray();
        for(Comment comment: seq.getComments()){
            JSONObject commentObj = new JSONObject();
            if(comment.getComment().indexOf("::") != -1){
                String comm[] = comment.getComment().split("\n");
                for(int i = 0; i < comm.length; i++){
                    if(comm[i].matches("(.*)\\s+::\\s+(.*)")){
                        String[] metaData = comm[i].split("::");
                        String key = metaData[0].trim();
                        String value = metaData[1].trim();
                        if(key.contains(".")){
                            key = key.replaceAll("\\.", " ");
                        }
                        commentMetaData.put(key, value);
                    }
                }
                commentObj.put("commentMeta", commentMetaData);
            }else{
                commentObj.put("comment", comment.getComment());
            }
            comments.put(commentObj);
        }
        doc.put("comments", comments);
    }
}

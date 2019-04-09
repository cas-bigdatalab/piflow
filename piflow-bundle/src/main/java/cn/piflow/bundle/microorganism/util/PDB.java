package cn.piflow.bundle.microorganism.util;

import org.apache.hadoop.fs.FSDataInputStream;
import org.apache.hadoop.fs.FileSystem;
import org.apache.hadoop.fs.Path;
import org.apache.log4j.Logger;
import org.biojava.nbio.structure.*;
import org.biojava.nbio.structure.io.PDBFileReader;
import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStreamReader;
import java.text.DateFormat;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.*;

public class PDB {

    static final Logger logger = Logger.getLogger(PDB.class);

    static final DateFormat formatter = new SimpleDateFormat("yyyy-MM-dd");
    static final DateFormat pdbdateformatter = new SimpleDateFormat("dd-MMM-yy", Locale.US);
    static final String NEWLINE = System.getProperty("line.separator");
    private JSONObject doc;
    private String pdbFilePath;
    private FileSystem fs;

    public PDB(String path,FileSystem f){
        this.pdbFilePath = path;
        this.doc = new JSONObject();
        this.fs = f;
        parsePDB();
    }

    public JSONObject getDoc(){
        return this.doc;
    }

    public void parsePDB(){
        //FileInputStream fileInputStream = null;
        parsePDBBioJava();
        parsePDBByLine();
    }

    private void parsePDBByLine(){
        try{
//            FileInputStream fileInputStream = new FileInputStream(pdbFilePath);
            FSDataInputStream fis = fs.open(new Path(pdbFilePath));
//            GZIPInputStream gzipout = new GZIPInputStream(fis);
            BufferedReader br = new BufferedReader(new InputStreamReader(fis));
            String line;
            while ((line = br.readLine()) != null){
                // ignore empty lines
                if ( line.equals("") ||
                        (line.equals(NEWLINE))){
                    continue;
                }

                // ignore short TER and END lines
                if ( (line.startsWith("TER")) ||
                        (line.startsWith("END"))) {
                    continue;
                }
                if ( line.length() < 6) {
                    logger.info("Found line length below 6. Ignoring it, line: >" + line +"<" );
                    continue;
                }
                String recordName = line.substring(0, 6).trim();
                if(recordName.equals("HET")){
                    het_Handler(line);
                }else if(recordName.equals("REVDAT")){
                    revdat_Handler(line);
                }else if(recordName.equals("SEQRES")){
                    seqres_Handler(line);
                }else if(recordName.equals("MODRES")){
                    modres_Handler(line);
                }else if(recordName.equals("HETNAM")){
                    hetnam_Handler(line);
                }else if(recordName.equals("HELIX")){
                    helix_Handler(line);
                }else if(recordName.equals("MASTER")){
                    master_Handler(line);
                }else if(recordName.equals("COMPND")){
                    continue;
                }
            }
        } catch (FileNotFoundException e) {
            e.printStackTrace();
        } catch (IOException e) {
            e.printStackTrace();
        } catch (ParseException e) {
            logger.error("parsing error in processing: " + pdbFilePath);
            logger.error(e.getMessage());
            //e.printStackTrace();
        }
    }

    //fields biojava processed
    private void parsePDBBioJava(){
        PDBFileReader pdbreader = new PDBFileReader();
        //set parsing parameters
        /*FileParsingParameters fileParsingParameters = new FileParsingParameters();
        fileParsingParameters.setAlignSeqRes(true);
        pdbreader.setFileParsingParameters(fileParsingParameters);*/
        try{
            //Structure struc = pdbreader.getStructure(pdbFilePath);
//            FileInputStream fileInputStream = new FileInputStream(pdbFilePath);
            FSDataInputStream fis = fs.open(new Path(pdbFilePath));
//            GZIPInputStream gzipout = new GZIPInputStream(fis);
            Structure struc = pdbreader.getStructure(fis);
            PDBHeader pdbHeader = struc.getPDBHeader();
            doc.put("DepositionDate", formatter.format(pdbHeader.getDepDate()));
            String depositionYear = doc.getString("DepositionDate").substring(0, 4);
            write_to_obj(doc, depositionYear, "DepositionYear");
            doc.put("Classification", pdbHeader.getClassification());
            doc.put("Idcode", pdbHeader.getIdCode());

            doc.put("ReferenceTitle", pdbHeader.getTitle());
            JSONArray compounds = new JSONArray();
            for(Compound c : struc.getCompounds()){
                JSONObject compound = new JSONObject();
                compound.put("MOLID", c.getMolId());
                compound.put("MoleculeName", c.getMolName());
                String compound_Chain = "";
                for(Chain chain : c.getChains()){
                    compound_Chain += ("," + chain.getChainID());
                }
                if(!compound_Chain.equals("")){
                    compound.put("Chain", compound_Chain.substring(1));
                }
                compound.put("Engineered", c.getEngineered());
                compounds.put(compound);
            }
            doc.put("Compounds", compounds);

            if(pdbHeader.getExperimentalTechniques() != null){
                Iterator<ExperimentalTechnique> experimentalTechniqueIterator = pdbHeader.getExperimentalTechniques().iterator();
                List<String> techniques = new ArrayList<String>();
                while (experimentalTechniqueIterator.hasNext()){
                    techniques.add(experimentalTechniqueIterator.next().getName());
                }
                doc.put("Techiques", techniques);
            }

            doc.put("Author", pdbHeader.getAuthors());

            JSONArray sites = new JSONArray();
            for(Site site : struc.getSites()){
                JSONObject siteObject = new JSONObject();
                siteObject.put("SiteIdentifier", site.getSiteID());
                siteObject.put("SiteDescription", site.getDescription());
                sites.put(siteObject);
            }
            doc.put("sites", sites);

            JSONArray dbRefs = new JSONArray();
            for(DBRef dbRef : struc.getDBRefs()){
                JSONObject dbRefObject = new JSONObject();
                dbRefObject.put("ChainID", dbRef.getChainId());
                dbRefObject.put("SeqBegin", dbRef.getSeqBegin());
                dbRefObject.put("SeqEnd", dbRef.getSeqEnd());
                dbRefObject.put("DbName", dbRef.getDatabase());
                dbRefObject.put("DbAccession", dbRef.getDbAccession());
                dbRefObject.put("DbSeqBegin", dbRef.getDbSeqBegin());
                dbRefObject.put("DbSeqEnd", dbRef.getDbSeqEnd());
                dbRefs.put(dbRefObject);
            }
            doc.put("dbRefs", dbRefs);
        } catch (Exception e) {
            logger.error("parsing error in processing: " + pdbFilePath);
            logger.error(e.getMessage());
            e.printStackTrace();
        }
    }

    private void het_Handler(String line){
        JSONObject hetObject = new JSONObject();
        String hetID = line.substring(7, 10).trim();
        String chainID = line.substring(12, 13);
        String seqNum = line.substring(14, 17).trim();
        String numHetAtoms = line.substring(21, 25).trim();
        hetObject.put("HetID", hetID);
        hetObject.put("ChainID", chainID);
        hetObject.put("SeqNum", seqNum);
        hetObject.put("NumHetAtoms", numHetAtoms);
        write_to_doc("hets", hetObject);
    }

    private void revdat_Handler(String line) throws ParseException {

        JSONObject revdatObject = new JSONObject();
        String modNumber = line.substring(8, 10).trim();
        write_to_obj(revdatObject, modNumber, "Modificationumber");
        String modDateStr = line.substring (13, 22).trim();
        if(!modDateStr.equals("")){
            Date modDate = pdbdateformatter.parse(modDateStr);
            revdatObject.put("ModificationDate", formatter.format(modDate));
        }
        write_to_doc("revdats", revdatObject);
    }

    private void seqres_Handler(String line){
        JSONObject seqresObject = new JSONObject();
        String chainID    = line.substring(11, 12);
        String numRes   = line.substring(13,17).trim();
        String acidSeq = line.substring(18).trim();
        seqresObject.put("chainID", chainID);
        write_to_obj(seqresObject, numRes, "NumRes");
        seqresObject.put("AcidSeq", acidSeq);
        write_to_doc("seqreses", seqresObject);
    }

    private void modres_Handler(String line){
        JSONObject modresObject = new JSONObject();
        // MODRES : MODRES 10MH 5NC C  427   DC  5-AZA-CYTIDINE-5'MONOPHOSPHATE
        String resName = line.substring(12, 15).trim();
        String chainID = line.substring(16, 17);
        String seqNum = line.substring(18, 22).trim();
        String stdRes = line.substring(23, 27).trim();
        String modComment = line.substring(28).trim();
        modresObject.put("ChainID", chainID);
        modresObject.put("ResName", resName);
        write_to_obj(modresObject, seqNum, "SeqNumber");
        modresObject.put("StdRes", stdRes);
        modresObject.put("ModificationComment", modComment);
        write_to_doc("modreses", modresObject);

    }

    private void hetnam_Handler(String line){
        JSONObject hetnamObject = new JSONObject();
        String hetID = line.substring(10, 14).trim();
        String chemicalName = line.substring(15).trim();
        hetnamObject.put("HetID", hetID);
        hetnamObject.put("ChemicalName", chemicalName);
        write_to_doc("hetnams", hetnamObject);
    }

    private void helix_Handler(String line){
        JSONObject helixObject = new JSONObject();
        String helixID = line.substring(12, 14).trim();
        if(line.trim().length() >= 40){
            String helixClass = line.substring(39, 40);
            write_to_obj(helixObject,helixClass,"HelixClass");
        }
        if (line.trim().length()>=76) {
            String helixLength = line.substring(72, 76).trim();
            write_to_obj(helixObject,helixLength, "HelixLength");
        }
        helixObject.put("HelixID", helixID);
        write_to_doc("helixes", helixObject);
    }

    private void master_Handler(String line){
        JSONObject masterObject = new JSONObject();
        String numRemark = line.substring(11,15).trim();
        String numHet = line.substring(21, 25).trim();
        String numHelix = line.substring(26, 30).trim();
        String numSheet = line.substring(31, 35).trim();
        String numTurn = line.substring(36, 40).trim();
        String numSite = line.substring(41, 45).trim();
        String numXForm = line.substring(46, 50).trim();
        String numCoord = line.substring(51, 55).trim();
        String numtTer = line.substring(56, 60).trim();
        String numConect = line.substring(61, 65).trim();
        String numSeq = line.substring(66, 70).trim();
        write_to_obj(masterObject, numRemark, "NumRemark");
        write_to_obj(masterObject, numHet, "NumHet");
        write_to_obj(masterObject, numHelix, "numHelix");
        write_to_obj(masterObject, numSheet, "NumSheet");
        write_to_obj(masterObject, numTurn, "NumTurn");
        write_to_obj(masterObject, numSite, "NumSite");
        write_to_obj(masterObject, numXForm, "NumXForm");
        write_to_obj(masterObject, numCoord, "NumCoord");
        write_to_obj(masterObject, numtTer, "NumtTer");
        write_to_obj(masterObject, numConect, "NumConect");
        write_to_obj(masterObject, numSeq, "NumSeq");
        write_to_doc("masters", masterObject);
    }
    private static void write_to_obj(JSONObject obj, String str, String key){
        int val;
        try{
            val = Integer.parseInt(str);
            obj.put(key, val);
        }catch (NumberFormatException fe){
            logger.error("parse integer error with string: " + str);
        }
    }

    private void write_to_doc(String array_name, JSONObject obj){
        if(doc.optJSONArray(array_name) != null){
            doc.getJSONArray(array_name).put(obj);
        }else{
            JSONArray arr = new JSONArray();
            arr.put(obj);
            doc.put(array_name, arr);
        }
    }
}

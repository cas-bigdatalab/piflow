package cn.piflow.bundle.microorganism.util;

import org.biojava.bio.BioError;
import org.biojava.bio.BioException;
import org.biojava.bio.seq.*;
import org.biojava.bio.seq.io.SymbolTokenization;
import org.biojava.bio.symbol.Alphabet;
import org.biojava.bio.symbol.AlphabetManager;
import org.biojava.utils.ChangeVetoException;
import org.biojavax.Namespace;
import org.biojavax.bio.BioEntry;
import org.biojavax.bio.seq.RichSequence;
import org.biojavax.bio.seq.RichSequenceIterator;
import org.biojavax.bio.seq.io.*;

import java.io.*;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;

/**
 * Created by xiujuan on 2016/1/28.
 */
public interface CustomIOTools {

    /**
     * A set of convenience methods for handling common file formats.
     *
     * @author Mark Schreiber
     * @author Richard Holland
     * @since 1.5
     */
    public final class IOTools {

        private static RichSequenceBuilderFactory factory = RichSequenceBuilderFactory.FACTORY;

        // This can't be instantiated.
        private IOTools() {
        }

        /**
         * Register a new format with IOTools for auto-guessing.
         *
         * @param formatClass
         *            the <code>RichSequenceFormat</code> object to register.
         */
        public static void registerFormat(Class formatClass) {
            Object o;
            try {
                o = formatClass.newInstance();
            } catch (Exception e) {
                throw new BioError(e);
            }
            if (!(o instanceof RichSequenceFormat))
                throw new BioError("Class " + formatClass
                        + " is not an implementation of RichSequenceFormat!");
            formatClasses.add(formatClass);
        }

        // Private reference to the formats we know about.
        private static List<Class> formatClasses = new ArrayList<Class>();

        /**
         * Guess which format a stream is then attempt to read it.
         *
         * @param stream
         *            the <code>BufferedInputStream</code> to attempt to read.
         * @param seqFactory
         *            a factory used to build a <code>RichSequence</code>
         * @param ns
         *            a <code>Namespace</code> to load the sequences into. Null
         *            implies that it should use the namespace specified in the
         *            file. If no namespace is specified in the file, then
         *            <code>RichObjectFactory.getDefaultNamespace()</code> is
         *            used.
         * @return a <code>RichSequenceIterator</code> over each sequence in the
         *         file
         * @throws IOException
         *             in case the stream is unrecognisable or problems occur in
         *             reading it.
         */
        public static RichSequenceIterator readStream(
                BufferedInputStream stream,
                RichSequenceBuilderFactory seqFactory, Namespace ns)
                throws IOException {
            for (Iterator<Class> i = formatClasses.iterator(); i.hasNext();) {
                Class formatClass = i.next();
                RichSequenceFormat format;
                try {
                    format = (RichSequenceFormat) formatClass.newInstance();
                } catch (Exception e) {
                    throw new BioError(e);
                }
                if (format.canRead(stream)) {
                    SymbolTokenization sTok = format
                            .guessSymbolTokenization(stream);
                    BufferedReader br = new BufferedReader(
                            new InputStreamReader(stream));
                    return new RichStreamReader(br, format, sTok, seqFactory,
                            ns);
                }
            }
            throw new IOException("Could not recognise format of stream.");
        }

        /**
         * Guess which format a stream is then attempt to read it.
         *
         * @return a <code>RichSequenceIterator</code> over each sequence in the
         *         file
         * @param stream
         *            the <code>BufferedInputStream</code> to attempt to read.
         * @param ns
         *            a <code>Namespace</code> to load the sequences into. Null
         *            implies that it should use the namespace specified in the
         *            file. If no namespace is specified in the file, then
         *            <code>RichObjectFactory.getDefaultNamespace()</code> is
         *            used.
         * @throws IOException
         *             If the file cannot be read.
         */
        public static RichSequenceIterator readStream(
                BufferedInputStream stream, Namespace ns) throws IOException {
            return readStream(stream, factory, ns);
        }

        /**
         * Guess which format a file is then attempt to read it.
         *
         * @param file
         *            the <code>File</code> to attempt to read.
         * @param seqFactory
         *            a factory used to build a <code>RichSequence</code>
         * @param ns
         *            a <code>Namespace</code> to load the sequences into. Null
         *            implies that it should use the namespace specified in the
         *            file. If no namespace is specified in the file, then
         *            <code>RichObjectFactory.getDefaultNamespace()</code> is
         *            used.
         * @return a <code>RichSequenceIterator</code> over each sequence in the
         *         file
         * @throws IOException
         *             in case the file is unrecognisable or problems occur in
         *             reading it.
         */
        public static RichSequenceIterator readFile(File file,
                                                    RichSequenceBuilderFactory seqFactory, Namespace ns)
                throws IOException {
            for (Iterator<Class> i = formatClasses.iterator(); i.hasNext();) {
                Class formatClass = i.next();
                RichSequenceFormat format;
                try {
                    format = (RichSequenceFormat) formatClass.newInstance();
                } catch (Exception e) {
                    throw new BioError(e);
                }
                if (format.canRead(file)) {
                    SymbolTokenization sTok = format
                            .guessSymbolTokenization(file);
                    BufferedReader br = new BufferedReader(new FileReader(file));
                    return new RichStreamReader(br, format, sTok, seqFactory,
                            ns);
                }
            }
            throw new IOException("Could not recognise format of file: "
                    + file.getName());
        }

        /**
         * Guess which format a file is then attempt to read it.
         *
         * @return a <code>RichSequenceIterator</code> over each sequence in the
         *         file
         * @param file
         *            the <code>File</code> to attempt to read.
         * @param ns
         *            a <code>Namespace</code> to load the sequences into. Null
         *            implies that it should use the namespace specified in the
         *            file. If no namespace is specified in the file, then
         *            <code>RichObjectFactory.getDefaultNamespace()</code> is
         *            used.
         * @throws IOException
         *             If the file cannot be read.
         */
        public static RichSequenceIterator readFile(File file, Namespace ns)
                throws IOException {
            return readFile(file, factory, ns);
        }

        /**
         * Read a fasta file.
         *
         * @param br
         *            the <code>BufferedReader<code> to read data from
         * @param sTok
         *            a <code>SymbolTokenization</code> that understands the
         *            sequences
         * @param ns
         *            a <code>Namespace</code> to load the sequences into. Null
         *            implies that it should use the namespace specified in the
         *            file. If no namespace is specified in the file, then
         *            <code>RichObjectFactory.getDefaultNamespace()</code> is
         *            used.
         * @return a <code>RichSequenceIterator</code> over each sequence in the
         *         fasta file
         */
        public static RichSequenceIterator readFasta(BufferedReader br,
                                                     SymbolTokenization sTok, Namespace ns) {
            return new RichStreamReader(br, new FastaFormat(), sTok, factory,
                    ns);
        }

        /**
         * Read a fasta file building a custom type of <code>RichSequence</code>
         * . For example, use <code>RichSequenceBuilderFactory.FACTORY</code> to
         * emulate <code>readFasta(BufferedReader, SymbolTokenization)</code>
         * and <code>RichSequenceBuilderFactory.PACKED</code> to force all
         * symbols to be encoded using bit-packing.
         *
         * @param br
         *            the <code>BufferedReader</code> to read data from
         * @param sTok
         *            a <code>SymbolTokenization</code> that understands the
         *            sequences
         * @param seqFactory
         *            a factory used to build a <code>RichSequence</code>
         * @param ns
         *            a <code>Namespace</code> to load the sequences into. Null
         *            implies that it should use the namespace specified in the
         *            file. If no namespace is specified in the file, then
         *            <code>RichObjectFactory.getDefaultNamespace()</code> is
         *            used.
         * @return a <code>RichSequenceIterator</code> over each sequence in the
         *         fasta file
         */
        public static RichSequenceIterator readFasta(BufferedReader br,
                                                     SymbolTokenization sTok, RichSequenceBuilderFactory seqFactory,
                                                     Namespace ns) {
            return new RichStreamReader(br, new FastaFormat(), sTok,
                    seqFactory, ns);
        }

        /**
         * Iterate over the sequences in an FASTA-format stream of DNA
         * sequences.
         *
         * @param br
         *            the <code>BufferedReader</code> to read data from
         * @param ns
         *            a <code>Namespace</code> to load the sequences into. Null
         *            implies that it should use the namespace specified in the
         *            file. If no namespace is specified in the file, then
         *            <code>RichObjectFactory.getDefaultNamespace()</code> is
         *            used.
         * @return a <code>RichSequenceIterator</code> over each sequence in the
         *         fasta file
         * @see #readHashedFastaDNA(BufferedInputStream, Namespace) for a
         *      speeded up version that can access sequences from memory.
         */
        public static RichSequenceIterator readFastaDNA(BufferedReader br,
                                                        Namespace ns) {
            return new RichStreamReader(br, new FastaFormat(), getDNAParser(),
                    factory, ns);
        }

        /**
         * Iterate over the sequences in an FASTA-format stream of DNA
         * sequences. In contrast to readFastaDNA, this provides a speeded up
         * implementation where all sequences are accessed from memory.
         *
         * @param is
         *            the <code>BufferedInputStream</code> to read data from
         * @param ns
         *            a <code>Namespace</code> to load the sequences into. Null
         *            implies that it should use the namespace specified in the
         *            file. If no namespace is specified in the file, then
         *            <code>RichObjectFactory.getDefaultNamespace()</code> is
         *            used.
         * @return a <code>RichSequenceIterator</code> over each sequence in the
         *         fasta file
         * @throws BioException
         *             if somethings goes wrong while reading the file.
         * @see #readFastaDNA
         */
        public static RichSequenceIterator readHashedFastaDNA(
                BufferedInputStream is, Namespace ns) throws BioException {

            Alphabet alpha = AlphabetManager.alphabetForName("DNA");
            return new HashedFastaIterator(is, alpha, ns);

        }

        /**
         * Iterate over the sequences in an FASTA-format stream of RNA
         * sequences.
         *
         * @param br
         *            the <code>BufferedReader</code> to read data from
         * @param ns
         *            a <code>Namespace</code> to load the sequences into. Null
         *            implies that it should use the namespace specified in the
         *            file. If no namespace is specified in the file, then
         *            <code>RichObjectFactory.getDefaultNamespace()</code> is
         *            used.
         * @return a <code>RichSequenceIterator</code> over each sequence in the
         *         fasta file
         */
        public static RichSequenceIterator readFastaRNA(BufferedReader br,
                                                        Namespace ns) {
            return new RichStreamReader(br, new FastaFormat(), getRNAParser(),
                    factory, ns);
        }

        /**
         * Iterate over the sequences in an FASTA-format stream of Protein
         * sequences.
         *
         * @param br
         *            the <code>BufferedReader</code> to read data from
         * @param ns
         *            a <code>Namespace</code> to load the sequences into. Null
         *            implies that it should use the namespace specified in the
         *            file. If no namespace is specified in the file, then
         *            <code>RichObjectFactory.getDefaultNamespace()</code> is
         *            used.
         * @return a <code>RichSequenceIterator</code> over each sequence in the
         *         fasta file
         */
        public static RichSequenceIterator readFastaProtein(BufferedReader br,
                                                            Namespace ns) {
            return new RichStreamReader(br, new FastaFormat(),
                    getProteinParser(), factory, ns);
        }

        /**
         * Read a GenBank file using a custom type of SymbolList. For example,
         * use RichSequenceBuilderFactory.FACTORY to emulate
         * readFasta(BufferedReader, SymbolTokenization) and
         * RichSequenceBuilderFactory.PACKED to force all symbols to be encoded
         * using bit-packing.
         *
         * @param br
         *            the <code>BufferedReader</code> to read data from
         * @param sTok
         *            a <code>SymbolTokenization</code> that understands the
         *            sequences
         * @param seqFactory
         *            a factory used to build a <code>SymbolList</code>
         * @param ns
         *            a <code>Namespace</code> to load the sequences into. Null
         *            implies that it should use the namespace specified in the
         *            file. If no namespace is specified in the file, then
         *            <code>RichObjectFactory.getDefaultNamespace()</code> is
         *            used.
         * @return a <code>RichSequenceIterator</code> over each see in the
         *         fasta file
         */
        public static RichSequenceIterator readGenbank(BufferedReader br,
                                                       SymbolTokenization sTok, RichSequenceBuilderFactory seqFactory,
                                                       Namespace ns) {
            return new RichStreamReader(br, new GenbankFormat(), sTok,
                    seqFactory, ns);
        }

        /*public static RichSequenceIterator readGenbank(BufferedReader br,
                                                       Namespace ns) {

        }*/

        /**
         * Iterate over the sequences in an GenBank-format stream of DNA
         * sequences.
         *
         * @param br
         *            the <code>BufferedReader</code> to read data from
         * @param ns
         *            a <code>Namespace</code> to load the sequences into. Null
         *            implies that it should use the namespace specified in the
         *            file. If no namespace is specified in the file, then
         *            <code>RichObjectFactory.getDefaultNamespace()</code> is
         *            used.
         * @return a <code>RichSequenceIterator</code> over each sequence in the
         *         fasta file
         */
        public static RichSequenceIterator readGenbankDNA(BufferedReader br,
                                                          Namespace ns) {
            return new RichStreamReader(br, new CustomGenbankFormat(),
                    getDNAParser(), factory, ns);

        }

        /**
         * Iterate over the sequences in an GenBank-format stream of RNA
         * sequences.
         *
         * @param br
         *            the <code>BufferedReader</code> to read data from
         * @param ns
         *            a <code>Namespace</code> to load the sequences into. Null
         *            implies that it should use the namespace specified in the
         *            file. If no namespace is specified in the file, then
         *            <code>RichObjectFactory.getDefaultNamespace()</code> is
         *            used.
         * @return a <code>RichSequenceIterator</code> over each sequence in the
         *         fasta file
         */
        public static RichSequenceIterator readGenbankRNA(BufferedReader br,
                                                          Namespace ns) {
            return new RichStreamReader(br, new GenbankFormat(),
                    getRNAParser(), factory, ns);
        }

        /**
         * Iterate over the sequences in an GenBank-format stream of Protein
         * sequences.
         *
         * @param br
         *            the <code>BufferedReader</code> to read data from
         * @param ns
         *            a <code>Namespace</code> to load the sequences into. Null
         *            implies that it should use the namespace specified in the
         *            file. If no namespace is specified in the file, then
         *            <code>RichObjectFactory.getDefaultNamespace()</code> is
         *            used.
         * @return a <code>RichSequenceIterator</code> over each sequence in the
         *         fasta file
         */
        public static RichSequenceIterator readGenbankProtein(
                BufferedReader br, Namespace ns) {
            return new RichStreamReader(br, new CustomGenbankFormat(),
                    getProteinParser(), factory, ns);
        }

        /**
         * Read a INSDseq file using a custom type of SymbolList. For example,
         * use RichSequenceBuilderFactory.FACTORY to emulate
         * readFasta(BufferedReader, SymbolTokenization) and
         * RichSequenceBuilderFactory.PACKED to force all symbols to be encoded
         * using bit-packing.
         *
         * @param br
         *            the <code>BufferedReader</code> to read data from
         * @param sTok
         *            a <code>SymbolTokenization</code> that understands the
         *            sequences
         * @param seqFactory
         *            a factory used to build a <code>SymbolList</code>
         * @param ns
         *            a <code>Namespace</code> to load the sequences into. Null
         *            implies that it should use the namespace specified in the
         *            file. If no namespace is specified in the file, then
         *            <code>RichObjectFactory.getDefaultNamespace()</code> is
         *            used.
         * @return a <code>RichSequenceIterator</code> over each sequence in the
         *         fasta file
         */
        public static RichSequenceIterator readINSDseq(BufferedReader br,
                                                       SymbolTokenization sTok, RichSequenceBuilderFactory seqFactory,
                                                       Namespace ns) {
            return new RichStreamReader(br, new INSDseqFormat(), sTok,
                    seqFactory, ns);
        }

        /**
         * Iterate over the sequences in an INSDseq-format stream of DNA
         * sequences.
         *
         * @param br
         *            the <code>BufferedReader</code> to read data from
         * @param ns
         *            a <code>Namespace</code> to load the sequences into. Null
         *            implies that it should use the namespace specified in the
         *            file. If no namespace is specified in the file, then
         *            <code>RichObjectFactory.getDefaultNamespace()</code> is
         *            used.
         * @return a <code>RichSequenceIterator</code> over each sequence in the
         *         fasta file
         */
        public static RichSequenceIterator readINSDseqDNA(BufferedReader br,
                                                          Namespace ns) {
            return new RichStreamReader(br, new INSDseqFormat(),
                    getDNAParser(), factory, ns);
        }

        /**
         * Iterate over the sequences in an INSDseq-format stream of RNA
         * sequences.
         *
         * @param br
         *            the <code>BufferedReader</code> to read data from
         * @param ns
         *            a <code>Namespace</code> to load the sequences into. Null
         *            implies that it should use the namespace specified in the
         *            file. If no namespace is specified in the file, then
         *            <code>RichObjectFactory.getDefaultNamespace()</code> is
         *            used.
         * @return a <code>RichSequenceIterator</code> over each sequence in the
         *         fasta file
         */
        public static RichSequenceIterator readINSDseqRNA(BufferedReader br,
                                                          Namespace ns) {
            return new RichStreamReader(br, new INSDseqFormat(),
                    getRNAParser(), factory, ns);
        }

        /**
         * Iterate over the sequences in an INSDseq-format stream of Protein
         * sequences.
         *
         * @param br
         *            the <code>BufferedReader</code> to read data from
         * @param ns
         *            a <code>Namespace</code> to load the sequences into. Null
         *            implies that it should use the namespace specified in the
         *            file. If no namespace is specified in the file, then
         *            <code>RichObjectFactory.getDefaultNamespace()</code> is
         *            used.
         * @return a <code>RichSequenceIterator</code> over each sequence in the
         *         fasta file
         */
        public static RichSequenceIterator readINSDseqProtein(
                BufferedReader br, Namespace ns) {
            return new RichStreamReader(br, new INSDseqFormat(),
                    getProteinParser(), factory, ns);
        }

        /**
         * Read a EMBLxml file using a custom type of SymbolList. For example,
         * use RichSequenceBuilderFactory.FACTORY to emulate
         * readFasta(BufferedReader, SymbolTokenization) and
         * RichSequenceBuilderFactory.PACKED to force all symbols to be encoded
         * using bit-packing.
         *
         * @param br
         *            the <code>BufferedReader</code> to read data from
         * @param sTok
         *            a <code>SymbolTokenization</code> that understands the
         *            sequences
         * @param seqFactory
         *            a factory used to build a <code>SymbolList</code>
         * @param ns
         *            a <code>Namespace</code> to load the sequences into. Null
         *            implies that it should use the namespace specified in the
         *            file. If no namespace is specified in the file, then
         *            <code>RichObjectFactory.getDefaultNamespace()</code> is
         *            used.
         * @return a <code>RichSequenceIterator</code> over each sequence in the
         *         fasta file
         */
        public static RichSequenceIterator readEMBLxml(BufferedReader br,
                                                       SymbolTokenization sTok, RichSequenceBuilderFactory seqFactory,
                                                       Namespace ns) {
            return new RichStreamReader(br, new EMBLxmlFormat(), sTok,
                    seqFactory, ns);
        }

        /**
         * Iterate over the sequences in an EMBLxml-format stream of DNA
         * sequences.
         *
         * @param br
         *            the <code>BufferedReader</code> to read data from
         * @param ns
         *            a <code>Namespace</code> to load the sequences into. Null
         *            implies that it should use the namespace specified in the
         *            file. If no namespace is specified in the file, then
         *            <code>RichObjectFactory.getDefaultNamespace()</code> is
         *            used.
         * @return a <code>RichSequenceIterator</code> over each sequence in the
         *         fasta file
         */
        public static RichSequenceIterator readEMBLxmlDNA(BufferedReader br,
                                                          Namespace ns) {
            return new RichStreamReader(br, new EMBLxmlFormat(),
                    getDNAParser(), factory, ns);
        }

        /**
         * Iterate over the sequences in an EMBLxml-format stream of RNA
         * sequences.
         *
         * @param br
         *            the <code>BufferedReader</code> to read data from
         * @param ns
         *            a <code>Namespace</code> to load the sequences into. Null
         *            implies that it should use the namespace specified in the
         *            file. If no namespace is specified in the file, then
         *            <code>RichObjectFactory.getDefaultNamespace()</code> is
         *            used.
         * @return a <code>RichSequenceIterator</code> over each sequence in the
         *         fasta file
         */
        public static RichSequenceIterator readEMBLxmlRNA(BufferedReader br,
                                                          Namespace ns) {
            return new RichStreamReader(br, new EMBLxmlFormat(),
                    getRNAParser(), factory, ns);
        }

        /**
         * Iterate over the sequences in an EMBLxml-format stream of Protein
         * sequences.
         *
         * @param br
         *            the <code>BufferedReader</code> to read data from
         * @param ns
         *            a <code>Namespace</code> to load the sequences into. Null
         *            implies that it should use the namespace specified in the
         *            file. If no namespace is specified in the file, then
         *            <code>RichObjectFactory.getDefaultNamespace()</code> is
         *            used.
         * @return a <code>RichSequenceIterator</code> over each sequence in the
         *         fasta file
         */
        public static RichSequenceIterator readEMBLxmlProtein(
                BufferedReader br, Namespace ns) {
            return new RichStreamReader(br, new EMBLxmlFormat(),
                    getProteinParser(), factory, ns);
        }

        /**
         * Read a EMBL file using a custom type of SymbolList. For example, use
         * RichSequenceBuilderFactory.FACTORY to emulate
         * readFasta(BufferedReader, SymbolTokenization) and
         * RichSequenceBuilderFactory.PACKED to force all symbols to be encoded
         * using bit-packing.
         *
         * @param br
         *            the <code>BufferedReader</code> to read data from
         * @param sTok
         *            a <code>SymbolTokenization</code> that understands the
         *            sequences
         * @param seqFactory
         *            a factory used to build a <code>SymbolList</code>
         * @param ns
         *            a <code>Namespace</code> to load the sequences into. Null
         *            implies that it should use the namespace specified in the
         *            file. If no namespace is specified in the file, then
         *            <code>RichObjectFactory.getDefaultNamespace()</code> is
         *            used.
         * @return a <code>RichSequenceIterator</code> over each sequence in the
         *         fasta file
         */
        public static RichSequenceIterator readEMBL(BufferedReader br,
                                                    SymbolTokenization sTok, RichSequenceBuilderFactory seqFactory,
                                                    Namespace ns) {
            return new RichStreamReader(br, new EMBLFormat(), sTok, seqFactory,
                    ns);
        }

        /**
         * Iterate over the sequences in an EMBL-format stream of DNA sequences.
         *
         * @param br
         *            the <code>BufferedReader</code> to read data from
         * @param ns
         *            a <code>Namespace</code> to load the sequences into. Null
         *            implies that it should use the namespace specified in the
         *            file. If no namespace is specified in the file, then
         *            <code>RichObjectFactory.getDefaultNamespace()</code> is
         *            used.
         * @return a <code>RichSequenceIterator</code> over each sequence in the
         *         fasta file
         */
        public static RichSequenceIterator readEMBLDNA(BufferedReader br,
                                                       Namespace ns) {
            return new RichStreamReader(br, new CustomEMBLFormat(), getDNAParser(),
                    factory, ns);
        }


        //parse Ensembl file
        public static RichSequenceIterator readEnsembl(BufferedReader br,
                                                       Namespace ns) {
            return new RichStreamReader(br, new CustomEnsemblFormat(), getDNAParser(),
                    factory, ns);
        }

        /**
         * Iterate over the sequences in an EMBL-format stream of RNA sequences.
         *
         * @param br
         *            the <code>BufferedReader</code> to read data from
         * @param ns
         *            a <code>Namespace</code> to load the sequences into. Null
         *            implies that it should use the namespace specified in the
         *            file. If no namespace is specified in the file, then
         *            <code>RichObjectFactory.getDefaultNamespace()</code> is
         *            used.
         * @return a <code>RichSequenceIterator</code> over each sequence in the
         *         fasta file
         */
        public static RichSequenceIterator readEMBLRNA(BufferedReader br,
                                                       Namespace ns) {
            return new RichStreamReader(br, new EMBLFormat(), getRNAParser(),
                    factory, ns);
        }

        /**
         * Iterate over the sequences in an EMBL-format stream of Protein
         * sequences.
         *
         * @param br
         *            the <code>BufferedReader</code> to read data from
         * @param ns
         *            a <code>Namespace</code> to load the sequences into. Null
         *            implies that it should use the namespace specified in the
         *            file. If no namespace is specified in the file, then
         *            <code>RichObjectFactory.getDefaultNamespace()</code> is
         *            used.
         * @return a <code>RichSequenceIterator</code> over each sequence in the
         *         fasta file
         */
        public static RichSequenceIterator readEMBLProtein(BufferedReader br,
                                                           Namespace ns) {
            return new RichStreamReader(br, new EMBLFormat(),
                    getProteinParser(), factory, ns);
        }

        /**
         * Read a UniProt file using a custom type of SymbolList. For example,
         * use RichSequenceBuilderFactory.FACTORY to emulate
         * readFasta(BufferedReader, SymbolTokenization) and
         * RichSequenceBuilderFactory.PACKED to force all symbols to be encoded
         * using bit-packing.
         *
         * @param br
         *            the <code>BufferedReader</code> to read data from
         * @param sTok
         *            a <code>SymbolTokenization</code> that understands the
         *            sequences
         * @param seqFactory
         *            a factory used to build a <code>SymbolList</code>
         * @param ns
         *            a <code>Namespace</code> to load the sequences into. Null
         *            implies that it should use the namespace specified in the
         *            file. If no namespace is specified in the file, then
         *            <code>RichObjectFactory.getDefaultNamespace()</code> is
         *            used.
         * @return a <code>RichSequenceIterator</code> over each sequence in the
         *         fasta file
         */
        public static RichSequenceIterator readUniProt(BufferedReader br,
                                                       SymbolTokenization sTok, RichSequenceBuilderFactory seqFactory,
                                                       Namespace ns) {
            return new RichStreamReader(br, new UniProtFormat(), sTok,
                    seqFactory, ns);
        }

        /**
         * Iterate over the sequences in an UniProt-format stream of RNA
         * sequences.
         *
         * @param br
         *            the <code>BufferedReader</code> to read data from
         * @param ns
         *            a <code>Namespace</code> to load the sequences into. Null
         *            implies that it should use the namespace specified in the
         *            file. If no namespace is specified in the file, then
         *            <code>RichObjectFactory.getDefaultNamespace()</code> is
         *            used.
         * @return a <code>RichSequenceIterator</code> over each sequence in the
         *         fasta file
         */
        public static RichSequenceIterator readUniProt(BufferedReader br,
                                                       Namespace ns) {
            return new RichStreamReader(br, new CustomUniProtFormat(),
                    getProteinParser(), factory, ns);
        }

        /**
         * Read a UniProt XML file using a custom type of SymbolList. For
         * example, use RichSequenceBuilderFactory.FACTORY to emulate
         * readFasta(BufferedReader, SymbolTokenization) and
         * RichSequenceBuilderFactory.PACKED to force all symbols to be encoded
         * using bit-packing.
         *
         * @param br
         *            the <code>BufferedReader</code> to read data from
         * @param sTok
         *            a <code>SymbolTokenization</code> that understands the
         *            sequences
         * @param seqFactory
         *            a factory used to build a <code>SymbolList</code>
         * @param ns
         *            a <code>Namespace</code> to load the sequences into. Null
         *            implies that it should use the namespace specified in the
         *            file. If no namespace is specified in the file, then
         *            <code>RichObjectFactory.getDefaultNamespace()</code> is
         *            used.
         * @return a <code>RichSequenceIterator</code> over each sequence in the
         *         fasta file
         */
        public static RichSequenceIterator readUniProtXML(BufferedReader br,
                                                          SymbolTokenization sTok, RichSequenceBuilderFactory seqFactory,
                                                          Namespace ns) {
            return new RichStreamReader(br, new UniProtXMLFormat(), sTok,
                    seqFactory, ns);
        }

        /**
         * Iterate over the sequences in an UniProt XML-format stream of RNA
         * sequences.
         *
         * @param br
         *            the <code>BufferedReader</code> to read data from
         * @param ns
         *            a <code>Namespace</code> to load the sequences into. Null
         *            implies that it should use the namespace specified in the
         *            file. If no namespace is specified in the file, then
         *            <code>RichObjectFactory.getDefaultNamespace()</code> is
         *            used.
         * @return a <code>RichSequenceIterator</code> over each sequence in the
         *         fasta file
         */
        public static RichSequenceIterator readUniProtXML(BufferedReader br,
                                                          Namespace ns) {
            return new RichStreamReader(br, new UniProtXMLFormat(),
                    getProteinParser(), factory, ns);
        }

        /**
         * Writes <CODE>Sequence</CODE>s from a <code>SequenceIterator</code> to
         * an <code>OutputStream </code>in Fasta Format. This makes for a useful
         * format filter where a <code>StreamReader</code> can be sent to the
         * <code>RichStreamWriter</code> after formatting.
         *
         * @param os
         *            The stream to write fasta formatted data to
         * @param in
         *            The source of input <CODE>RichSequence</CODE>s
         * @param ns
         *            a <code>Namespace</code> to write the
         *            <CODE>RichSequence</CODE>s to. <CODE>Null</CODE> implies
         *            that it should use the namespace specified in the
         *            individual sequence.
         * @param header
         *            the FastaHeader
         * @throws IOException
         *             if there is an IO problem
         */
        public static void writeFasta(OutputStream os, SequenceIterator in,
                                      Namespace ns, FastaHeader header) throws IOException {
            FastaFormat fastaFormat = new FastaFormat();
            if (header != null) {
                fastaFormat.setHeader(header);
            }
            RichStreamWriter sw = new RichStreamWriter(os, fastaFormat);
            sw.writeStream(in, ns);
        }

        /**
         * Writes <CODE>Sequence</CODE>s from a <code>SequenceIterator</code> to
         * an <code>OutputStream </code>in Fasta Format. This makes for a useful
         * format filter where a <code>StreamReader</code> can be sent to the
         * <code>RichStreamWriter</code> after formatting.
         *
         * @param os
         *            The stream to write fasta formatted data to
         * @param in
         *            The source of input <CODE>RichSequence</CODE>s
         * @param ns
         *            a <code>Namespace</code> to write the
         *            <CODE>RichSequence</CODE>s to. <CODE>Null</CODE> implies
         *            that it should use the namespace specified in the
         *            individual sequence.
         * @throws IOException
         *             if there is an IO problem
         */
        public static void writeFasta(OutputStream os, SequenceIterator in,
                                      Namespace ns) throws IOException {
            writeFasta(os, in, ns, null);
        }

        /**
         * Writes a single <code>Sequence</code> to an <code>OutputStream</code>
         * in Fasta format.
         *
         * @param os
         *            the <code>OutputStream</code>.
         * @param seq
         *            the <code>Sequence</code>.
         * @param ns
         *            a <code>Namespace</code> to write the sequences to. Null
         *            implies that it should use the namespace specified in the
         *            individual sequence.
         * @throws IOException
         *             if there is an IO problem
         */
        public static void writeFasta(OutputStream os, Sequence seq,
                                      Namespace ns) throws IOException {
            writeFasta(os, new SingleRichSeqIterator(seq), ns, null);
        }

        /**
         * Writes a single <code>Sequence</code> to an <code>OutputStream</code>
         * in Fasta format.
         *
         * @param os
         *            the <code>OutputStream</code>.
         * @param seq
         *            the <code>Sequence</code>.
         * @param ns
         *            a <code>Namespace</code> to write the sequences to. Null
         *            implies that it should use the namespace specified in the
         *            individual sequence.
         * @param header
         *            a <code>FastaHeader</code> that controls the fields in the
         *            header.
         * @throws IOException
         *             if there is an IO problem
         */
        public static void writeFasta(OutputStream os, Sequence seq,
                                      Namespace ns, FastaHeader header) throws IOException {
            writeFasta(os, new SingleRichSeqIterator(seq), ns, header);
        }

        /**
         * Writes sequences from a <code>SequenceIterator</code> to an
         * <code>OutputStream </code>in GenBank Format. This makes for a useful
         * format filter where a <code>StreamReader</code> can be sent to the
         * <code>RichStreamWriter</code> after formatting.
         *
         * @param os
         *            The stream to write fasta formatted data to
         * @param in
         *            The source of input Sequences
         * @param ns
         *            a <code>Namespace</code> to write the sequences to. Null
         *            implies that it should use the namespace specified in the
         *            individual sequence.
         * @throws IOException
         *             if there is an IO problem
         */
        public static void writeGenbank(OutputStream os, SequenceIterator in,
                                        Namespace ns) throws IOException {
            RichStreamWriter sw = new RichStreamWriter(os, new GenbankFormat());
            sw.writeStream(in, ns);
        }

        /**
         * Writes a single <code>Sequence</code> to an <code>OutputStream</code>
         * in GenBank format.
         *
         * @param os
         *            the <code>OutputStream</code>.
         * @param seq
         *            the <code>Sequence</code>.
         * @param ns
         *            a <code>Namespace</code> to write the sequences to. Null
         *            implies that it should use the namespace specified in the
         *            individual sequence.
         * @throws IOException
         *             if there is an IO problem
         */
        public static void writeGenbank(OutputStream os, Sequence seq,
                                        Namespace ns) throws IOException {
            writeGenbank(os, new SingleRichSeqIterator(seq), ns);
        }

        /**
         * Writes sequences from a <code>SequenceIterator</code> to an
         * <code>OutputStream </code>in INSDseq Format. This makes for a useful
         * format filter where a <code>StreamReader</code> can be sent to the
         * <code>RichStreamWriter</code> after formatting.
         *
         * @param os
         *            The stream to write fasta formatted data to
         * @param in
         *            The source of input Sequences
         * @param ns
         *            a <code>Namespace</code> to write the sequences to. Null
         *            implies that it should use the namespace specified in the
         *            individual sequence.
         * @throws IOException
         *             if there is an IO problem
         */
        public static void writeINSDseq(OutputStream os, SequenceIterator in,
                                        Namespace ns) throws IOException {
            RichStreamWriter sw = new RichStreamWriter(os, new INSDseqFormat());
            sw.writeStream(in, ns);
        }

        /**
         * Writes a single <code>Sequence</code> to an <code>OutputStream</code>
         * in INSDseq format.
         *
         * @param os
         *            the <code>OutputStream</code>.
         * @param seq
         *            the <code>Sequence</code>.
         * @param ns
         *            a <code>Namespace</code> to write the sequences to. Null
         *            implies that it should use the namespace specified in the
         *            individual sequence.
         * @throws IOException
         *             if there is an IO problem
         */
        public static void writeINSDseq(OutputStream os, Sequence seq,
                                        Namespace ns) throws IOException {
            writeINSDseq(os, new SingleRichSeqIterator(seq), ns);
        }

        /**
         * Writes sequences from a <code>SequenceIterator</code> to an
         * <code>OutputStream </code>in EMBLxml Format. This makes for a useful
         * format filter where a <code>StreamReader</code> can be sent to the
         * <code>RichStreamWriter</code> after formatting.
         *
         * @param os
         *            The stream to write fasta formatted data to
         * @param in
         *            The source of input Sequences
         * @param ns
         *            a <code>Namespace</code> to write the sequences to. Null
         *            implies that it should use the namespace specified in the
         *            individual sequence.
         * @throws IOException
         *             if there is an IO problem
         */
        public static void writeEMBLxml(OutputStream os, SequenceIterator in,
                                        Namespace ns) throws IOException {
            RichStreamWriter sw = new RichStreamWriter(os, new EMBLxmlFormat());
            sw.writeStream(in, ns);
        }

        /**
         * Writes a single <code>Sequence</code> to an <code>OutputStream</code>
         * in EMBLxml format.
         *
         * @param os
         *            the <code>OutputStream</code>.
         * @param seq
         *            the <code>Sequence</code>.
         * @param ns
         *            a <code>Namespace</code> to write the sequences to. Null
         *            implies that it should use the namespace specified in the
         *            individual sequence.
         * @throws IOException
         *             if there is an IO problem
         */
        public static void writeEMBLxml(OutputStream os, Sequence seq,
                                        Namespace ns) throws IOException {
            writeEMBLxml(os, new SingleRichSeqIterator(seq), ns);
        }

        /**
         * Writes sequences from a <code>SequenceIterator</code> to an
         * <code>OutputStream </code>in EMBL Format. This makes for a useful
         * format filter where a <code>StreamReader</code> can be sent to the
         * <code>RichStreamWriter</code> after formatting.
         *
         * @param os
         *            The stream to write fasta formatted data to
         * @param in
         *            The source of input Sequences
         * @param ns
         *            a <code>Namespace</code> to write the sequences to. Null
         *            implies that it should use the namespace specified in the
         *            individual sequence.
         * @throws IOException
         *             if there is an IO problem
         */
        public static void writeEMBL(OutputStream os, SequenceIterator in,
                                     Namespace ns) throws IOException {
            RichStreamWriter sw = new RichStreamWriter(os, new EMBLFormat());
            sw.writeStream(in, ns);
        }

        /**
         * Writes a single <code>Sequence</code> to an <code>OutputStream</code>
         * in EMBL format.
         *
         * @param os
         *            the <code>OutputStream</code>.
         * @param seq
         *            the <code>Sequence</code>.
         * @param ns
         *            a <code>Namespace</code> to write the sequences to. Null
         *            implies that it should use the namespace specified in the
         *            individual sequence.
         * @throws IOException
         *             if there is an IO problem
         */
        public static void writeEMBL(OutputStream os, Sequence seq, Namespace ns)
                throws IOException {
            writeEMBL(os, new SingleRichSeqIterator(seq), ns);
        }

        /**
         * Writes sequences from a <code>SequenceIterator</code> to an
         * <code>OutputStream </code>in UniProt Format. This makes for a useful
         * format filter where a <code>StreamReader</code> can be sent to the
         * <code>RichStreamWriter</code> after formatting.
         *
         * @param os
         *            The stream to write fasta formatted data to
         * @param in
         *            The source of input Sequences
         * @param ns
         *            a <code>Namespace</code> to write the sequences to. Null
         *            implies that it should use the namespace specified in the
         *            individual sequence.
         * @throws IOException
         *             if there is an IO problem
         */
        public static void writeUniProt(OutputStream os, SequenceIterator in,
                                        Namespace ns) throws IOException {
            RichStreamWriter sw = new RichStreamWriter(os, new UniProtFormat());
            sw.writeStream(in, ns);
        }

        /**
         * Writes a single <code>Sequence</code> to an <code>OutputStream</code>
         * in UniProt format.
         *
         * @param os
         *            the <code>OutputStream</code>.
         * @param seq
         *            the <code>Sequence</code>.
         * @param ns
         *            a <code>Namespace</code> to write the sequences to. Null
         *            implies that it should use the namespace specified in the
         *            individual sequence.
         * @throws IOException
         *             if there is an IO problem
         */
        public static void writeUniProt(OutputStream os, Sequence seq,
                                        Namespace ns) throws IOException {
            writeUniProt(os, new SingleRichSeqIterator(seq), ns);
        }

        /**
         * Writes sequences from a <code>SequenceIterator</code> to an
         * <code>OutputStream </code>in UniProt XML Format. This makes for a
         * useful format filter where a <code>StreamReader</code> can be sent to
         * the <code>RichStreamWriter</code> after formatting.
         *
         * @param os
         *            The stream to write fasta formatted data to
         * @param in
         *            The source of input Sequences
         * @param ns
         *            a <code>Namespace</code> to write the sequences to. Null
         *            implies that it should use the namespace specified in the
         *            individual sequence.
         * @throws IOException
         *             if there is an IO problem
         */
        public static void writeUniProtXML(OutputStream os,
                                           SequenceIterator in, Namespace ns) throws IOException {
            RichStreamWriter sw = new RichStreamWriter(os,
                    new UniProtXMLFormat());
            sw.writeStream(in, ns);
        }

        /**
         * Writes a single <code>Sequence</code> to an <code>OutputStream</code>
         * in UniProt XML format.
         *
         * @param os
         *            the <code>OutputStream</code>.
         * @param seq
         *            the <code>Sequence</code>.
         * @param ns
         *            a <code>Namespace</code> to write the sequences to. Null
         *            implies that it should use the namespace specified in the
         *            individual sequence.
         * @throws IOException
         *             if there is an IO problem
         */
        public static void writeUniProtXML(OutputStream os, Sequence seq,
                                           Namespace ns) throws IOException {
            writeUniProtXML(os, new SingleRichSeqIterator(seq), ns);
        }

        /**
         * Creates a DNA symbol tokenizer.
         *
         * @return a <code>SymbolTokenization</code> for parsing DNA.
         */
        public static SymbolTokenization getDNAParser() {
            try {
                return DNATools.getDNA().getTokenization("token");
            } catch (BioException ex) {
                throw new BioError("Assertion failing:"
                        + " Couldn't get DNA token parser", ex);
            }
        }

        /**
         * Creates a RNA symbol tokenizer.
         *
         * @return a <code>SymbolTokenization</code> for parsing RNA.
         */
        public static SymbolTokenization getRNAParser() {
            try {
                return RNATools.getRNA().getTokenization("token");
            } catch (BioException ex) {
                throw new BioError("Assertion failing:"
                        + " Couldn't get RNA token parser", ex);
            }
        }

        /**
         * Creates a nucleotide symbol tokenizer.
         *
         * @return a <code>SymbolTokenization</code> for parsing nucleotides.
         */
        public static SymbolTokenization getNucleotideParser() {
            try {
                return NucleotideTools.getNucleotide().getTokenization("token");
            } catch (BioException ex) {
                throw new BioError("Assertion failing:"
                        + " Couldn't get nucleotide token parser", ex);
            }
        }

        /**
         * Creates a protein symbol tokenizer.
         *
         * @return a <code>SymbolTokenization</code> for parsing protein.
         */
        public static SymbolTokenization getProteinParser() {
            try {
                return ProteinTools.getTAlphabet().getTokenization("token");
            } catch (BioException ex) {
                throw new BioError("Assertion failing:"
                        + " Couldn't get PROTEIN token parser", ex);
            }
        }

        /**
         * Used to iterate over a single rich sequence
         */
        public static final class SingleRichSeqIterator implements
                RichSequenceIterator {

            private RichSequence seq;

            /**
             * Creates an iterator over a single sequence.
             *
             * @param seq
             *            the sequence to iterate over.
             */
            public SingleRichSeqIterator(Sequence seq) {
                try {
                    if (seq instanceof RichSequence)
                        this.seq = (RichSequence) seq;
                    else
                        this.seq = RichSequence.Tools.enrich(seq);
                } catch (ChangeVetoException e) {
                    throw new RuntimeException("Unable to enrich sequence", e);
                }
            }

            /**
             * {@inheritDoc}
             *
             * @return true if another <CODE>RichSequence</CODE> is available
             */
            public boolean hasNext() {
                return seq != null;
            }

            /**
             * {@inheritDoc}
             *
             * @return a <CODE>RichSequence</CODE>
             */
            public Sequence nextSequence() {
                return this.nextRichSequence();
            }

            /**
             * {@inheritDoc}
             *
             * @return a <CODE>RichSequence</CODE>
             */
            public BioEntry nextBioEntry() {
                return this.nextRichSequence();
            }

            /**
             * {@inheritDoc}
             *
             * @return a <CODE>RichSequence</CODE>
             */
            public RichSequence nextRichSequence() {
                RichSequence seq = this.seq;
                this.seq = null;
                return seq;
            }
        }
    }
}

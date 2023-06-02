package cn.piflow.bundle.FluxJavaUtil;


import org.apache.commons.math3.stat.regression.OLSMultipleLinearRegression;

public class Theleastsquaremethod {


    /*
     y 常量
     x 变量
     */
    public static double[] train(double[] y,double[][] x) {
//        double[] y = new double[]{2.9, 3.0, 4.8, 1.8, 2.9,4.9,4.2,4.8,4.4,4.5};
//        double[][] x = new double[10][2];


        OLSMultipleLinearRegression oregression = new OLSMultipleLinearRegression();
        oregression.newSampleData(y,x);

//        z = a + bx + cy  数组beta中的值按顺序依次代表回归方程中的常量a、x1系数b、x2系数c，
        double[] beta = oregression.estimateRegressionParameters();

        double b0 = beta[0];
        double b1 = beta[0];
        double b2 = beta[0];

       return  beta;
    }



    public static double[] train1() {
        double[] y = new double[]{2.9, 3.0, 4.8, 1.8, 2.9,4.9,4.2,4.8,4.4,4.5};
        double[][] x = new double[10][2];

        x[0] = new double[]{2, 1};
        x[1] = new double[]{6, 0};
        x[2] = new double[]{8, 1};
        x[3] = new double[]{3, 0};
        x[4] = new double[]{2, 1};
        x[5] = new double[]{7, 1};
        x[6] = new double[]{9, 0};
        x[7] = new double[]{8, 0};
        x[8] = new double[]{4, 1};
        x[9] = new double[]{6, 1};
        OLSMultipleLinearRegression oregression = new OLSMultipleLinearRegression();
        oregression.newSampleData(y,x);

//        z = a + bx + cy  数组beta中的值按顺序依次代表回归方程中的常量a、x1系数b、x2系数c，
        double[] beta = oregression.estimateRegressionParameters();

        double b0 = beta[0];
        double b1 = beta[0];
        double b2 = beta[0];

        return  beta;
    }



    public static void main(String args[]) {
//        double[] x = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9};
//        double[] y = {23, 44, 32, 56, 33, 34, 55, 65, 45, 55};
//        Theleastsquaremethod.train(x, y);
//        System.out.println(Theleastsquaremethod.predict(10.0));






    }
}

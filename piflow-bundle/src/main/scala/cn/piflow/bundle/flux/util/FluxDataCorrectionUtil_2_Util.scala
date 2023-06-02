package cn.piflow.bundle.flux.util

import breeze.linalg.DenseMatrix
import breeze.numerics._


class FluxDataCorrectionUtil_2_Util extends Serializable {

  // 3.1:坐标轴旋转  DR
  def DRUtil(p06:Double,p07:Double,p08:Double,p09:Double,p10:Double,p11:Double,p12:Double,p13:Double,p14:Double,p15:Double,p16:Double,p17:Double,
                           p18:Double,p19:Double,p20:Double,
                           p24:Double,p25:Double,p26:Double): Array[Double] ={
    //    𝑢0、𝑣0、𝑤0为校正前三维风速
    val u0= p24
    val v0= p25
    val w0= p26

    val suv = sqrt(pow(u0,2)+pow(v0,2))
    val suvw = sqrt(pow(u0,2)+pow(v0,2)+pow(w0,2))

    val r11: Double = u0/suvw
    val r12: Double = v0/suvw
    val r13: Double = w0/suvw

    val r21: Double = -v0/suv
    val r22: Double = u0/suv
    val r23: Double = 0

    val r31: Double = (-u0*w0)/(suvw*suv)
    val r32: Double = (-v0*w0)/(suvw*suv)
    val r33: Double = suv/suvw

    //   CO2通量  坐标旋转
    val Fcr = r31*p14 + r32*p18 + r33*p09
    //    潜热通量 坐标旋转
    val LE  = r31*p15 + r32*p19 + r33*p10
    //  显热通量 坐标旋转
    val Hs  = r31*p16 + r32*p20 + r33*p11

    val r02: DenseMatrix[Double] = DenseMatrix((r11 ,r12 ,r13), (r21 ,r22 ,r23), (r31 ,r32 ,r33))
    val r02t= r02.t
    val originMatrix: DenseMatrix[Double] = DenseMatrix((p12 ,p13 ,p07), (p13 ,p17 ,p08), (p07 ,p08 ,p06))

    val value: DenseMatrix[Double] = r02 * originMatrix * r02t
    val p12r = value(0,0)
    val p13r = value(0,1)
    val p07r = value(0,2)
    val p17r = value(1,1)
    val p08r = value(1,2)
    val p06r = value(2,2)

    val ustar_r = sqrt(sqrt(pow(p07r,2)+pow(p08r,2)))

    val pfDouble = Array[Double](Fcr,LE,Hs,ustar_r)
    pfDouble
  }




  // 3.2 坐标轴旋转  PF
  def PFUtil(p06:Double,p07:Double,p08:Double,p09:Double,p10:Double,p11:Double,p12:Double,p13:Double,p14:Double,p15:Double,p16:Double,p17:Double,
                           p18:Double,p19:Double,p20:Double,b1:Double,b2:Double): Array[Double] ={

    val e = sqrt(pow(b1,2)+pow(b2,2)+1)
    val r31: Double = -b1/e
    val r32: Double = -b2/e
    val r33: Double =  1/e

    val ca = sqrt(pow(r32,2)+pow(r33,2))
    val r11: Double = ca
    val r12: Double = (-r31*r32) / ca
    val r13: Double = (-r31*r33) / ca

    val r21: Double = 0
    val r22: Double = r33/ca
    val r23: Double = -r32 /ca

    //   CO2通量  坐标旋转
    val Fcr = r31*p14 + r32*p18 + r33*p09
    //    潜热通量 坐标旋转
    val LE  = r31*p15 + r32*p19 + r33*p10
    //  显热通量 坐标旋转
    val Hs  = r31*p16 + r32*p20 + r33*p11

    val r02: DenseMatrix[Double] = DenseMatrix((r11 ,r12 ,r13), (r21 ,r22 ,r23), (r31 ,r32 ,r33))
    val r02t= r02.t
    val originMatrix: DenseMatrix[Double] = DenseMatrix((p12 ,p13 ,p07), (p13 ,p17 ,p08), (p07 ,p08 ,p06))

    val value: DenseMatrix[Double] = r02 * originMatrix * r02t
    val p12r = value(0,0)
    val p13r = value(0,1)
    val p07r = value(0,2)
    val p17r = value(1,1)
    val p08r = value(1,2)
    val p06r = value(2,2)

    val ustar_r = sqrt(sqrt(pow(p07r,2)+pow(p08r,2)))

    val pfDouble = Array[Double](Fcr,LE,Hs,ustar_r)
    pfDouble
  }


  // WPL 校正
  def wplUtil(FC:Double,LE:Double,Hs:Double,p27:Double,p28:Double,p29:Double,p30:Double): Array[Double] ={
    val md = 28.966
    val mv = 18

    val u = md/mv

    val pc = p27
//    val pv = p28
    val pv = p28 * 1000
//    val pa = p30
    val pa = p30 * 1000 * 1000

    val pd = pa-pv
    val q = pv/pd

//    由超声温度[p29]转换为空气温度
    val T = (p29+273.15)/(1+0.51*pv/pa)
//    val T = p29 + 273.15
//    显热通量
    val wpv = LE
//    潜热通量
    val wT=  Hs

    // 对 CO2通量进行校正
    val FC_wpl = (pc*md)/(pd*mv)*wpv + ( 1+ (pv*md)/(pd*mv) ) * (pc/T) * wT

    //    对 潜热通量进行校正
    var LE_wpl =(1+ (pv*md)/(pd*mv) )* (wpv + (pv/T)/1000 *wT)

    //  显热通量量纲转换
    val Lv= 2440
//    ta = T - 273.15
//    val Lv = -0.002 * ta*ta - 2.2191*ta + 2498.4
    LE_wpl = Lv * LE_wpl

    // 对 潜热通量进行量纲转换
    val Cp = 1.00467
    val Hs_wpl = Cp * pa * Hs / 1000

//    println(FC_wpl)
    println(FC+FC_wpl,LE_wpl,Hs_wpl)

    val wplDouble = Array[Double](FC+FC_wpl,LE_wpl,Hs_wpl)
    wplDouble
  }



}

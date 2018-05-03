package util

/**
	* Created by bluejoe on 2017/9/30.
	*/
object ReflectUtils {
	implicit def reflected(o: AnyRef) = new ReflectedObject(o);

	def singleton[T](implicit m: Manifest[T]): AnyRef = {
		val field = Class.forName(m.runtimeClass.getName + "$").getDeclaredField("MODULE$");
		field.setAccessible(true);
		field.get();
	}

	def instanceOf[T](args: Any*)(implicit m: Manifest[T]): T = {
		val constructor = m.runtimeClass.getDeclaredConstructor(args.map(_.getClass): _*);
		constructor.setAccessible(true);
		constructor.newInstance(args.map(_.asInstanceOf[Object]): _*).asInstanceOf[T];
	}

	def instanceOf(className: String)(args: Any*) = {
		val constructor = Class.forName(className).getDeclaredConstructor(args.map(_.getClass): _*);
		constructor.setAccessible(true);
		constructor.newInstance(args.map(_.asInstanceOf[Object]): _*);
	}
}

class ReflectedObject(o: AnyRef) {
	//employee._get("company.name")
	def _get(name: String): AnyRef = {
		var o2 = o;
		for (fn <- name.split("\\.")) {
			val field = o2.getClass.getDeclaredField(fn);
			field.setAccessible(true);
			o2 = field.get(o2);
		}
		o2;
	}

	def _getLazy(name: String): AnyRef = {
		_call(s"${name}$$lzycompute")();
	}

	def _call(name: String)(args: Any*): AnyRef = {
		//val method = o.getClass.getDeclaredMethod(name, args.map(_.getClass): _*);
		//TODO: supports overloaded methods?
		val methods = o.getClass.getDeclaredMethods.filter(_.getName.equals(name));
		val method = methods(0);
		method.setAccessible(true);
		method.invoke(o, args.map(_.asInstanceOf[Object]): _*);
	}
}

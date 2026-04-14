import Img1 from "../images/agent1.jpg";
import Img2 from "../images/agent2.jpg";
import Img3 from "../images/agent3.jpg";

/* 流水线案例区 */
const Examples = () => {
  const pipelineExamples = [
    {
      title: "科研语料清洗",
      desc: "「去除干扰字符并进行分句处理」",
      img: Img1,
      alt: "Data Cleaning",
    },
    {
      title: "学术实体抽取",
      desc: "「提取所有的化学物质名称及描述」",
      img: Img2,
      alt: "Entity Extraction",
    },
    {
      title: "多模态数据对齐",
      desc: "「图表数据与文字描述语义关联」",
      img: Img3,
      alt: "Knowledge Graph",
    },
  ];

  return (
    <section className="px-8 pb-12">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-8">
          <h2 className="text-sm font-bold uppercase tracking-[0.2em] text-gray-900">
            选择加工流水线示例，一键体验
          </h2>
          <div className="w-12 h-0.5 bg-black mx-auto mt-3" />
        </div>
        <div className="grid grid-cols-3 gap-6">
          {pipelineExamples.map((item) => (
            <div
              key={item.title}
              className="border border-gray-100 p-4 hover:border-black transition-colors group cursor-pointer bg-white">
              <div className="aspect-video mb-3 bg-gray-50 flex items-center justify-center overflow-hidden">
                <img
                  alt={item.alt}
                  className="w-full h-full object-cover opacity-80 group-hover:scale-105 transition-transform"
                  src={item.img}
                />
              </div>
              <h3 className="text-[13px] font-bold mb-1">{item.title}</h3>
              <p className="text-[11px] text-[#6B7280] line-clamp-1">
                {item.desc}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Examples;

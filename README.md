# PyWbUnit

本模块提供Python与Workbench联合仿真的支持：可通过Python启动Workbench，并向WB实时发送脚本代码执行，同时支持查询代码执行结果和脚本变量值。

说明：本模块只提供Python与Workbench中的ScriptEngine的双向数据接口，WB中仿真功能实现还需要通过其Python脚本开发实现，可以参考以下文章：

- 《[基于Python的Workbench开发指南+案例解析](https://mp.weixin.qq.com/s?__biz=Mzg5MDMwNDIwMQ==&mid=2247483779&idx=1&sn=c6ccd8641b852364f0b87bef85f416e1&chksm=cfdfe225f8a86b33377a6bd9824c01d509772cdc0e86212be992634760dd0a715f9e0f7ff5a3&token=1162439082&lang=zh_CN#rd)》
- 《[Workbench开发指南：仿真流程集成](https://mp.weixin.qq.com/s?__biz=Mzg5MDMwNDIwMQ==&mid=2247483922&idx=1&sn=1b3e9d5e36abd1afbeff37493c472194&chksm=cfdfe1b4f8a868a225c2bd12cc67dfb59a5f7593af9d840b906b4d5391074a1bbfb26b680e1f&token=1162439082&lang=zh_CN#rd)》
- 《[Workbench开发指南：仿真模板开发](https://mp.weixin.qq.com/s?__biz=Mzg5MDMwNDIwMQ==&mid=2247483935&idx=1&sn=db6b79291216713f08104875b58906c5&chksm=cfdfe1b9f8a868afec0844cef84cb6f11b7a16e0d38fb7c305b7ce0ab6dddb35729298ca05de&token=1162439082&lang=zh_CN#rd)》
- 《[SCDM二次开发快速入门|应用+技巧](https://mp.weixin.qq.com/s?__biz=Mzg5MDMwNDIwMQ==&mid=2247483810&idx=1&sn=f88dc36cbb1296e0b45bdeb6a2c83325&chksm=cfdfe204f8a86b12be2bb476ba19a57a1074e4df5f7eb05df82cb0c81858e7db52e5a5cc2562&token=1162439082&lang=zh_CN#rd)》
- 《[轻松上手Mechanical脚本自动化](https://mp.weixin.qq.com/s?__biz=Mzg5MDMwNDIwMQ==&mid=2247484014&idx=1&sn=b122a0c8bcdde20c5632c04efb8cf1a4&chksm=cfdfe1c8f8a868de229aa8f3b05fb606dc00bf852d6de4336c9f148e4c786c540816072fb639&token=1162439082&lang=zh_CN#rd)》
- 《[Fluent脚本自动化快速入门](https://mp.weixin.qq.com/s?__biz=Mzg5MDMwNDIwMQ==&mid=2247483965&idx=1&sn=6b197e9c067f07cf111f37345e4c4f4f&chksm=cfdfe19bf8a8688dd53c5c9a721646956f820ea90fb33de92314cb91f01a3728ca609cf01b1e&token=1162439082&lang=zh_CN#rd)》


## 安装使用

预编译的二进制库目前只支持Windows x64平台的Python3.7、3.8版本，安装方法如下：
```batch
pip install PyWbUnit-0.2.0-cp37-none-win_amd64.whl
pip install PyWbUnit-0.2.0-cp38-none-win_amd64.whl
```

## 使用方法
首先从PyWbUnit模块中导入CoWbUnitProcess类，详细文档说明可以通过help(CoWbUnitProcess)查看，以公众号文章：《[ANSYS中使用Python实现高效结构仿真](https://mp.weixin.qq.com/s?__biz=Mzg5MDMwNDIwMQ==&mid=2247484455&idx=1&sn=aac9501bb6fec23276353e4a27c10af9&chksm=cfdfe781f8a86e97bc5afb34678036318ce09d442d82cbeab195c8bdbaeb9e3e00606951469c&token=1162439082&lang=zh_CN#rd)》为例，演示如何使用PyWbUnit调用Workbench完成联合仿真的过程：

```python
# -*- coding: utf-8 -*-
from PyWbUnit import CoWbUnitProcess

# 创建wb单元实例，指定ansys wb版本，如2020R1对应201
coWbUnit = CoWbUnitProcess(workDir=r'E:/Workdata', version=201)
coWbUnit.initialize()
command = 'mechSys = GetTemplate(TemplateName="Static Structural", Solver="ANSYS").CreateSystem()'
coWbUnit.execWbCommand(command)
coWbUnit.execWbCommand('systems=GetAllSystems()')
print(coWbUnit.queryWbVariable('systems'))
materialScript = r'''# 创建静结构分析流程
# 获得Engineering Data数据容器
engData = mechSys.GetContainer(ComponentName="Engineering Data")
# 封装创建材料的方法
def CreateMaterial(name, density, *elastic):
    mat = engData.CreateMaterial(Name=name)
    mat.CreateProperty(Name="Density").SetData(Variables=["Density"],
        Values=[["%s [kg m^-3]" % density]])
    elasticProp = mat.CreateProperty(Name="Elasticity", Behavior="Isotropic")
    elasticProp.SetData(Variables=["Young's Modulus"], Values=[["%s [MPa]" % elastic[0]]])
    elasticProp.SetData(Variables=["Poisson's Ratio"], Values=[["%s" % elastic[1]]])
# 创建材料Steel，密度：7850kg/m3，杨氏模量：208e3MPa，泊松比：0.3
CreateMaterial("Steel", 7850, 209.e3, 0.3)'''
coWbUnit.execWbCommand(materialScript)
coWbUnit.execWbCommand('geo=mechSys.GetContainer("Geometry")')
coWbUnit.execWbCommand('geo.Edit(IsSpaceClaimGeometry=True)')
geoScript = r'''# Python Script, API Version = V18
# 创建悬臂梁实体区域
BlockBody.Create(Point.Origin, Point.Create(MM(200), MM(25), MM(20)))
GetRootPart().SetName("Beam")
# 选择beam实体，用于后续材料赋予
Selection.Create(GetRootPart().Bodies).CreateAGroup("ns_beamBody")
# 通过坐标点选择面对象
def GetFaceObjByPt(pt):
    for face in GetRootPart().GetDescendants[IDesignFace]():
        if face.Shape.ContainsPoint(pt): return face
# 选择固定约束加载面
fixSupFace = GetFaceObjByPt(Point.Create(0, MM(12.5), MM(10)))
Selection.Create(fixSupFace).CreateAGroup("ns_fixSup")
# 选择压力载荷加载面
pressFace = GetFaceObjByPt(Point.Create(MM(50), MM(12.5), MM(20)))
Selection.Create(pressFace).CreateAGroup("ns_press")
'''
coWbUnit.execWbCommand(f'geo.SendCommand(Language="Python", Command={geoScript!r})')
coWbUnit.execWbCommand(f'geo.Exit()')
launchScript = r'''# 刷新Model Component数据
modelComp = mechSys.GetComponent(Name="Model")
modelComp.Refresh()
# 获得Mechanical中Model的数据容器
model = mechSys.GetContainer(ComponentName="Model")
model.Edit()'''
coWbUnit.execWbCommand(launchScript)
mechScript = r"""# encoding: utf-8
# 给定Named Selection名称获取子对象实例
def GetLocByName(ns_name):
    for ns in Model.NamedSelections.Children:
        if ns.Name == ns_name: return ns
# 指定材料
matAss = Model.Materials.AddMaterialAssignment()
matAss.Material = "Steel"
matAss.Location = GetLocByName("ns_beamBody")
# 划分网格
mesh = Model.Mesh
mesh.ElementSize = Quantity("10 [mm]")
mesh.GenerateMesh()
# 获得Analyses对象
analysis = Model.Analyses[0]
# 添加固定约束
fixSup = analysis.AddFixedSupport()
fixSup.Location= GetLocByName("ns_fixSup")
# 加载压力载荷
pressLoad = analysis.AddPressure()
pressLoad.Location = GetLocByName("ns_press")
pressLoad.Magnitude.Output.DiscreteValues = [Quantity("0.5 [MPa]")]
Model.Solve()
# 后处理操作
solution = analysis.Solution
misesResult = solution.AddEquivalentStress()
misesResult.EvaluateAllResults()
# 设置视角
camera = ExtAPI.Graphics.Camera
camera.UpVector = Vector3D(0,0,1)
camera.SceneWidth = Quantity("150 [mm]")
camera.SceneHeight = Quantity("120 [mm]")
camera.FocalPoint = Point((0.08,0.0125,0), 'm')
# 输出后处理云图
misesResult.Activate()
ExtAPI.Graphics.ExportImage("d:/mises.png")"""
coWbUnit.execWbCommand(f'model.SendCommand(Language="Python", Command={mechScript!r})')
coWbUnit.execWbCommand('model.Exit()')
coWbUnit.saveProject(r"E:/Workdata/beam.wbpj")
# 关闭wb单元实例
coWbUnit.finalize()
```

## 问题反馈

关注微信公众号：“ANSYS仿真与开发”，后台留言；或者邮件至：tguangs@163.com



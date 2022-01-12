# -*- coding: utf-8 -*-
from PyWbUnit import CoWbUnitProcess

coWbUnit = CoWbUnitProcess()
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
coWbUnit.finalize()

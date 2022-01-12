# -*- coding: utf-8 -*-
import shutil
from socket import *
import subprocess
import tempfile
import os
from pathlib import Path
from typing import Union
import time
from Errors import (handleException, CoWbUnitRuntimeError)


__all__ = ["CoWbUnitProcess", "WbServerClient", "__version__",
           "__author__"]

__version__ = ".".join(("0", "3", "0"))
__author__ = "tguangs@163.com"


class CoWbUnitProcess(object):

    """Unit class for co-simulation with Workbench using Python.

    >>> coWbUnit = CoWbUnitProcess()
    >>> coWbUnit.initialize()
    >>> command = 'GetTemplate(TemplateName="Static Structural", Solver="ANSYS").CreateSystem()'
    >>> coWbUnit.execWbCommand(command)
    >>> coWbUnit.execWbCommand('systems=GetAllSystems()')
    >>> print(coWbUnit.queryWbVariable('systems'))
    >>> coWbUnit.saveProject(r'D:/example.wbpj')
    >>> coWbUnit.finalize()
    """

    _aasName = "aaS_WbId.txt"

    def __init__(self, workDir=None, version=201, interactive=True):
        """
        Constructor of CoWbUnitProcess.
        :param interactive: bool, whether to open the Workbench in interactive mode.
        :param workDir: str, the directory where the Workbench starts.
        :param version: int, workbench version: 2019R1-190/2020R1-201/2021R1-211.
        :param interactive: bool, whether to display the Workbench interface
        """
        self._workDir = Path(workDir) if workDir else Path(".")
        if f"AWP_ROOT{version}" not in os.environ:
            raise CoWbUnitRuntimeError(f"ANSYS version: v{version} is not installed!")
        self._ansysDir = Path(os.environ[f"AWP_ROOT{version}"])
        self._wbExe = self._ansysDir / "Framework" / "bin" / "Win64" / "runwb2.exe"
        self._interactive = interactive
        self._process = None
        self._coWbUnit = None

    def _start(self):
        aasFile = self._workDir / self._aasName
        self._clear_aasFile()
        stateOpt = fr'''-p "[9000:9200]" --server-write-connection-info "{aasFile}"'''
        if self._interactive:
            batchArgs = fr'"{self._wbExe}" -I {stateOpt}'
        else:
            batchArgs = fr'"{self._wbExe}" -s {stateOpt}'
        self._process = subprocess.Popen(batchArgs, cwd=str(self._workDir.absolute()),
                                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    def _clear_aasFile(self):
        aasFile = self._workDir / self._aasName
        if aasFile.exists(): aasFile.unlink()

    def initialize(self) -> None:
        """Called before `execWbCommand`: Start the Workbench in interactive
        mode and open the TCP server port to create a socket connection
        :return: None
        """
        if self._coWbUnit is not None:
            raise RuntimeError("Workbench client already started!")
        self._start()
        self._coWbUnit = WbServerClient(self._readWbId())

    def execWbCommand(self, command: str) -> str:
        """Send python script command to the Workbench for execution
        :param command: str, python script command
        :return: str, execution result
        """
        if self._coWbUnit is None:
            raise CoWbUnitRuntimeError("Please initialize() first!")
        return self._coWbUnit.execWbCommand(command)

    def queryWbVariable(self, variable: str):
        """Query the value of `variable` in the workbench script environment
        :param variable: str, script variable name
        :return: str
        """
        return self._coWbUnit.queryWbVariable(variable)

    def terminate(self):
        """Terminates the current Workbench client process
        :return: bool
        """
        if self._process:
            try:
                self._process.terminate()
                tempDir = tempfile.mkdtemp()
                filePath = os.path.join(tempDir, "temp.wbpj")
                self.saveProject(filePath)
                self.finalize()
                while True:
                    try:
                        shutil.rmtree(tempDir)
                        break
                    except OSError:
                        time.sleep(2)
                return True
            except PermissionError:
                return False

    def saveProject(self, filePath=None, overWrite=True):
        """Save the current workbench project file to `filePath`
        If the Project has not been saved, using method: `saveProject()`
        will raise `CommandFailedException`
        :param filePath: Optional[str, None], if
        :param overWrite: bool, Whether to overwrite the original project
        :return: str, execution result
        """
        if filePath is None:
            return self.execWbCommand(f'Save(Overwrite={overWrite})')
        return self.execWbCommand(f'Save(FilePath={filePath!r}, Overwrite={overWrite})')

    def finalize(self):
        """
        Exit the current workbench and close the TCP Server connection
        :return: None
        """
        self.saveProject()
        self.exitWb()
        self._clear_aasFile()
        self._process = None
        self._coWbUnit = None

    def exitWb(self) -> str:
        """
        `Exit` the current Workbench client process
        :return: str
        """
        return self.execWbCommand("Exit")

    def _readWbId(self) -> Union[str, None]:
        if not self._process: return None
        aasFile = self._workDir / self._aasName
        while True:
            if not aasFile.exists():
                time.sleep(0.5)
                continue
            with aasFile.open("r") as data:
                for line in data:
                    if 'localhost' in line:
                        return line


class WbServerClient:

    """Client Class for the Workbench server connection
    >>> aas_key = 'localhost:9000'
    >>> wbClient = WbServerClient(aas_key)
    >>> wbClient.execWbCommand('<wb_python_command>')
    >>> print(wbClient.queryWbVariable('<wb_python_var>'))
    """

    _suffix = '<EOF>'
    _coding = 'UTF-8'
    _buffer = 1024

    def __init__(self, aasKey: str):
        aasList = aasKey.split(':')
        self._address = (aasList[0], int(aasList[1]))

    def execWbCommand(self, command: str) -> str:
        sockCommand = command + self._suffix

        with socket(AF_INET, SOCK_STREAM) as sock:
            sock.connect(self._address)
            sock.sendall(sockCommand.encode(self._coding))
            data = sock.recv(self._buffer).decode()

        if data != '<OK>' and 'Exception:' in data:
            raise handleException(data)
        return data

    def queryWbVariable(self, variable) -> str:
        self.execWbCommand("__variable__=" + variable + ".__repr__()")
        retValue = self.execWbCommand("Query,__variable__")
        return retValue[13:]

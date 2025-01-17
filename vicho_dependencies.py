import os
class DependenciesManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DependenciesManager, cls).__new__(cls)
            cls._instance.initialize()
        return cls._instance

    def initialize(self):
        self.clr = None
        
        self.List = None

        # TeximpNet stuff
        self.Surface = None
        self.Compressor = None
        self.CompressionFormat = None
        self.CompressionQuality = None
        self.OutputFileFormat = None
        self.MipmapFilter = None
        self.ImageFilter = None
        self.RoundMode = None

        # CodeWalker stuff
        self.GameFiles = None
        self.Utils = None

    @property
    def available(self):
        return all(
            [
                self.clr,
                self.List,
                self.Surface,
                self.Compressor,
                self.CompressionFormat,
                self.CompressionQuality,
                self.OutputFileFormat,
                self.MipmapFilter,
                self.ImageFilter,
                self.RoundMode,
                self.GameFiles,
                self.Utils,
            ]
        )

    def load_dependencies(self):
        try:
            p = os.path.dirname(__file__)
            runtime_loc = fr"{p}\libs\vichotools.json"
            libs_loc = fr"{p}\libs"
            os.environ["PATH"] = libs_loc + os.pathsep + os.environ["PATH"]
            if os.path.exists(runtime_loc):
                import pythonnet
                pythonnet.load("coreclr", runtime_config=runtime_loc)
            else:
                return False

            import clr

            print("CLR OK")

            clr.AddReference(fr'{libs_loc}\CodeWalker.Core.dll')
            clr.AddReference("System.Collections")
            clr.AddReference(fr'{libs_loc}\TeximpNet.dll')
            print("References added correctly")

            from System.Collections.Generic import List
            import CodeWalker.GameFiles as GameFiles
            import CodeWalker.Utils as Utils
            from TeximpNet import Surface as Surface, ImageFilter as ImageFilter
            from TeximpNet.Compression import (
                Compressor,
                CompressionFormat,
                CompressionQuality,
                OutputFileFormat,
                MipmapFilter,
                RoundMode
            )

            print("Modules OK")

            self.clr = clr

            self.GameFiles = GameFiles
            self.Utils = Utils
            
            self.List = List

            self.Surface = Surface
            self.Compressor = Compressor
            self.CompressionFormat = CompressionFormat
            self.CompressionQuality = CompressionQuality
            self.OutputFileFormat = OutputFileFormat
            self.MipmapFilter = MipmapFilter
            self.ImageFilter = ImageFilter
            self.RoundMode = RoundMode

            print("Dependencies loaded OK")
            print(f"dependencies.available: {self.available}")
            print(f"clr: {self.clr}")
            print(f"GameFiles: {self.GameFiles}")
            print(f"List: {self.List}")
            print(f"Utils: {self.Utils}")
            print(f"Surface: {self.Surface}")
            print(f"Compressor: {self.Compressor}")

            return True
        except Exception as e:
            print(f"Error detail: {e}")
            import traceback

            traceback.print_exc()
            return False


dependencies_manager = DependenciesManager()


def is_dotnet_installed():
    path_env = os.getenv("PATH")
    dotnet_runtime_path = None
    for path in path_env.split(os.pathsep):
        if os.path.isdir(path) and "dotnet" in path.lower():
            shared_path = os.path.join(path, "shared", "Microsoft.NETCore.App")
            if os.path.isdir(shared_path):
                dotnet_runtime_path = shared_path
                break
    if dotnet_runtime_path:
        for version in os.listdir(dotnet_runtime_path):
            if version.startswith("8."):
                coreclr_path = os.path.join(dotnet_runtime_path, version, "coreclr.dll")
                if os.path.isfile(coreclr_path):
                    return True
    return False


def is_pythonnet_loaded():
    try:
        import pythonnet

        return True
    except ImportError:
        return False

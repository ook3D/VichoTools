import os
from ...vicho_dependencies import dependencies_manager as d
from .misc import calculate_mipmaps_lvls, get_dds, closest_pow2_dims, closest_pow2
import bpy
from pathlib import Path

SUPPORTED_FORMATS = [
    ".png",
    ".jpg",
    ".bmp",
    ".tiff",
    ".tif",
    ".jpeg",
    ".dds",
    ".psd",
    ".gif",
    ".webp",
]


def texture_list_from_dds_files(ddsFiles: list[str]):
    textureList = d.List[d.GameFiles.Texture]()
    for ddsFile in ddsFiles:
        fn = ddsFile
        if not os.path.exists(fn):
            print("File not found: " + fn)
            continue
        try:
            with open(ddsFile, "rb") as dds_open:
                content = dds_open.read()
            byte_array = bytearray(content)
            tex = d.Utils.DDSIO.GetTexture(byte_array)
            tex.Name = os.path.splitext(os.path.basename(ddsFile))[0]
            tex.NameHash = d.GameFiles.JenkHash.GenHash(str(tex.Name.lower()))
            d.GameFiles.JenkIndex.Ensure(tex.Name.lower())
            textureList.Add(tex)
        except Exception as e:
            print(f"Error opening file {ddsFile}: {e}")
            continue
    return textureList


def textures_to_ytd(textureList, ytdFile):
    textureDictionary = ytdFile.TextureDict
    textureDictionary.BuildFromTextureList(textureList)
    return ytdFile

def is_transparent(image) -> bool:
    return image.IsTransparent


def convert_folder_to_ytd(folder: str):
    dds_files = get_dds(folder)
    ytd = d.GameFiles.YtdFile()
    ytd.TextureDict = d.GameFiles.TextureDictionary()
    ytd.TextureDict.Textures = d.GameFiles.ResourcePointerList64[d.GameFiles.Texture]()
    ytd.TextureDict.TextureNameHashes = d.GameFiles.ResourceSimpleList64_uint()
    final_ytd = textures_to_ytd(texture_list_from_dds_files(dds_files), ytd)
    return final_ytd


def convert_img_to_dds(filepath: str, file_ext: str, quality: str, do_max_dimension: bool, half_res: bool, max_res: int, output_path: str, is_tint: bool, resize_dds: bool):
    adv = bpy.context.scene.ytd_advanced_mode
    surface = None
    compressor = d.Compressor()
    
    img_filter = filter(lambda x: x != ".dds", SUPPORTED_FORMATS) if not resize_dds else SUPPORTED_FORMATS
    
    if file_ext in img_filter:
        try:
            print(f"Trying to load image {filepath}")
            surface = d.Surface.LoadFromFile(filepath, True)
        except Exception:
            print(f"Error loading image {filepath}")
            return None
    else:
        print(f"Invalid file extension {file_ext}")
        return None

    width, height = surface.Width, surface.Height
    if adv:
        if do_max_dimension:
            width, height = closest_pow2_dims(width, height, max_res, False)
        if half_res:
            width, height = closest_pow2_dims(width, height, 0, True)
        surface.Resize(width, height, d.ImageFilter.Lanczos3)
    else:
        width, height = closest_pow2(width), closest_pow2(height)
    mip_levels = calculate_mipmaps_lvls(width, height)
    compressor.Input.SetData(surface)
    compressor.Input.RoundMode = d.RoundMode.ToNearestPowerOfTwo
    print(f"Is tint: {is_tint} from {filepath}")
    if is_tint:
        compressor.Input.SetMipmapGeneration(False, 1)
        compressor.Compression.Format = d.CompressionFormat.BGRA
        
    else:
        compressor.Input.SetMipmapGeneration(True, mip_levels)
        compressor.Compression.Format = (
            d.CompressionFormat.DXT5
            if is_transparent(surface)
            else d.CompressionFormat.DXT1a
        )

    compressor.Compression.Quality = get_quality(quality)
    dds_name = os.path.join(output_path, Path(filepath).stem + ".dds")
    compressor.Process(dds_name)
    surface.Dispose()
    compressor.Dispose()


def get_quality(quality: str):
    match quality:
        case "FASTEST":
            return d.CompressionQuality.Fastest
        case "NORMAL":
            return d.CompressionQuality.Normal
        case "PRODUCTION":
            return d.CompressionQuality.Production
        case "HIGHEST":
            return d.CompressionQuality.Highest
        case _:
            return d.CompressionQuality.Normal

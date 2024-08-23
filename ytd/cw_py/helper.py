import math
from pathlib import Path
import os
from ...vicho_dependencies import dependencies_manager as d
from .misc import calculate_mipmaps_lvls, get_dds, closest_pow2_dims, closest_pow2
from ...misc.funcs import power_of_two_resize
import bpy

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


def resize_image(image):
    imageHeight: int = image.Height
    imageWidth: int = image.Width
    log2Width: float = math.log2(imageWidth)
    log2Height: float = math.log2(imageHeight)
    if log2Width % 1 == 0 and log2Height % 1 == 0:
        return image
    image_new_size = power_of_two_resize(imageWidth, imageHeight)
    image.Resize(image_new_size[0], image_new_size[1], d.ImageFilter.Lanczos3)
    return image


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


def convert_img_to_dds(filepath: str, quality: str, do_max_dimension: bool, half_res: bool, max_res: int):
    adv = bpy.context.scene.ytd_advanced_mode

    surface = None
    compressor = d.Compressor()
    fileExt = Path(filepath).suffix
    fileName = Path(filepath).stem
    if fileExt in filter(lambda x: x != ".dds", SUPPORTED_FORMATS):
        try:
            surface = d.Surface.LoadFromFile(filepath, True)
        except Exception:
            print(f"Error loading image {filepath}")
            return None
    else:
        print(f"Invalid file extension {fileExt}")
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
    compressor.Input.SetMipmapGeneration(True, mip_levels)
    compressor.Input.MipmapFilter = d.MipmapFilter.Box
    compressor.Output.OutputFileFormat = d.OutputFileFormat.DDS
    compressor.Compression.Quality = get_quality(quality)
    compressor.Compression.Format = (
        d.CompressionFormat.DXT5
        if is_transparent(surface)
        else d.CompressionFormat.DXT1a
    )

    output_path = os.path.join(os.path.dirname(filepath), f"{fileName}.dds")

    compressor.Process(output_path)

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

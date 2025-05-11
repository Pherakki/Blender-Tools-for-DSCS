from ...serialization.DSCSStructs import DSCSSerializable


class DXGIFormat:
    DXGI_FORMAT_UNKNOWN                                 = 0
    DXGI_FORMAT_R32G32B32A32_TYPELESS                   = 1
    DXGI_FORMAT_R32G32B32A32_FLOAT                      = 2
    DXGI_FORMAT_R32G32B32A32_UINT                       = 3
    DXGI_FORMAT_R32G32B32A32_SINT                       = 4
    DXGI_FORMAT_R32G32B32_TYPELESS                      = 5
    DXGI_FORMAT_R32G32B32_FLOAT                         = 6
    DXGI_FORMAT_R32G32B32_UINT                          = 7
    DXGI_FORMAT_R32G32B32_SINT                          = 8
    DXGI_FORMAT_R16G16B16A16_TYPELESS                   = 9
    DXGI_FORMAT_R16G16B16A16_FLOAT                      = 10
    DXGI_FORMAT_R16G16B16A16_UNORM                      = 11
    DXGI_FORMAT_R16G16B16A16_UINT                       = 12
    DXGI_FORMAT_R16G16B16A16_SNORM                      = 13
    DXGI_FORMAT_R16G16B16A16_SINT                       = 14
    DXGI_FORMAT_R32G32_TYPELESS                         = 15
    DXGI_FORMAT_R32G32_FLOAT                            = 16
    DXGI_FORMAT_R32G32_UINT                             = 17
    DXGI_FORMAT_R32G32_SINT                             = 18
    DXGI_FORMAT_R32G8X24_TYPELESS                       = 19
    DXGI_FORMAT_D32_FLOAT_S8X24_UINT                    = 20
    DXGI_FORMAT_R32_FLOAT_X8X24_TYPELESS                = 21
    DXGI_FORMAT_X32_TYPELESS_G8X24_UINT                 = 22
    DXGI_FORMAT_R10G10B10A2_TYPELESS                    = 23
    DXGI_FORMAT_R10G10B10A2_UNORM                       = 24
    DXGI_FORMAT_R10G10B10A2_UINT                        = 25
    DXGI_FORMAT_R11G11B10_FLOAT                         = 26
    DXGI_FORMAT_R8G8B8A8_TYPELESS                       = 27
    DXGI_FORMAT_R8G8B8A8_UNORM                          = 28
    DXGI_FORMAT_R8G8B8A8_UNORM_SRGB                     = 29
    DXGI_FORMAT_R8G8B8A8_UINT                           = 30
    DXGI_FORMAT_R8G8B8A8_SNORM                          = 31
    DXGI_FORMAT_R8G8B8A8_SINT                           = 32
    DXGI_FORMAT_R16G16_TYPELESS                         = 33
    DXGI_FORMAT_R16G16_FLOAT                            = 34
    DXGI_FORMAT_R16G16_UNORM                            = 35
    DXGI_FORMAT_R16G16_UINT                             = 36
    DXGI_FORMAT_R16G16_SNORM                            = 37
    DXGI_FORMAT_R16G16_SINT                             = 38
    DXGI_FORMAT_R32_TYPELESS                            = 39
    DXGI_FORMAT_D32_FLOAT                               = 40
    DXGI_FORMAT_R32_FLOAT                               = 41
    DXGI_FORMAT_R32_UINT                                = 42
    DXGI_FORMAT_R32_SINT                                = 43
    DXGI_FORMAT_R24G8_TYPELESS                          = 44
    DXGI_FORMAT_D24_UNORM_S8_UINT                       = 45
    DXGI_FORMAT_R24_UNORM_X8_TYPELESS                   = 46
    DXGI_FORMAT_X24_TYPELESS_G8_UINT                    = 47
    DXGI_FORMAT_R8G8_TYPELESS                           = 48
    DXGI_FORMAT_R8G8_UNORM                              = 49
    DXGI_FORMAT_R8G8_UINT                               = 50
    DXGI_FORMAT_R8G8_SNORM                              = 51
    DXGI_FORMAT_R8G8_SINT                               = 52
    DXGI_FORMAT_R16_TYPELESS                            = 53
    DXGI_FORMAT_R16_FLOAT                               = 54
    DXGI_FORMAT_D16_UNORM                               = 55
    DXGI_FORMAT_R16_UNORM                               = 56
    DXGI_FORMAT_R16_UINT                                = 57
    DXGI_FORMAT_R16_SNORM                               = 58
    DXGI_FORMAT_R16_SINT                                = 59
    DXGI_FORMAT_R8_TYPELESS                             = 60
    DXGI_FORMAT_R8_UNORM                                = 61
    DXGI_FORMAT_R8_UINT                                 = 62
    DXGI_FORMAT_R8_SNORM                                = 63
    DXGI_FORMAT_R8_SINT                                 = 64
    DXGI_FORMAT_A8_UNORM                                = 65
    DXGI_FORMAT_R1_UNORM                                = 66
    DXGI_FORMAT_R9G9B9E5_SHAREDEXP                      = 67
    DXGI_FORMAT_R8G8_B8G8_UNORM                         = 68
    DXGI_FORMAT_G8R8_G8B8_UNORM                         = 69
    DXGI_FORMAT_BC1_TYPELESS                            = 70
    DXGI_FORMAT_BC1_UNORM                               = 71
    DXGI_FORMAT_BC1_UNORM_SRGB                          = 72
    DXGI_FORMAT_BC2_TYPELESS                            = 73
    DXGI_FORMAT_BC2_UNORM                               = 74
    DXGI_FORMAT_BC2_UNORM_SRGB                          = 75
    DXGI_FORMAT_BC3_TYPELESS                            = 76
    DXGI_FORMAT_BC3_UNORM                               = 77
    DXGI_FORMAT_BC3_UNORM_SRGB                          = 78
    DXGI_FORMAT_BC4_TYPELESS                            = 79
    DXGI_FORMAT_BC4_UNORM                               = 80
    DXGI_FORMAT_BC4_SNORM                               = 81
    DXGI_FORMAT_BC5_TYPELESS                            = 82
    DXGI_FORMAT_BC5_UNORM                               = 83
    DXGI_FORMAT_BC5_SNORM                               = 84
    DXGI_FORMAT_B5G6R5_UNORM                            = 85
    DXGI_FORMAT_B5G5R5A1_UNORM                          = 86
    DXGI_FORMAT_B8G8R8A8_UNORM                          = 87
    DXGI_FORMAT_B8G8R8X8_UNORM                          = 88
    DXGI_FORMAT_R10G10B10_XR_BIAS_A2_UNORM              = 89
    DXGI_FORMAT_B8G8R8A8_TYPELESS                       = 90
    DXGI_FORMAT_B8G8R8A8_UNORM_SRGB                     = 91
    DXGI_FORMAT_B8G8R8X8_TYPELESS                       = 92
    DXGI_FORMAT_B8G8R8X8_UNORM_SRGB                     = 93
    DXGI_FORMAT_BC6H_TYPELESS                           = 94
    DXGI_FORMAT_BC6H_UF16                               = 95
    DXGI_FORMAT_BC6H_SF16                               = 96
    DXGI_FORMAT_BC7_TYPELESS                            = 97
    DXGI_FORMAT_BC7_UNORM                               = 98
    DXGI_FORMAT_BC7_UNORM_SRGB                          = 99
    DXGI_FORMAT_AYUV                                    = 100
    DXGI_FORMAT_Y410                                    = 101
    DXGI_FORMAT_Y416                                    = 102
    DXGI_FORMAT_NV12                                    = 103
    DXGI_FORMAT_P010                                    = 104
    DXGI_FORMAT_P016                                    = 105
    DXGI_FORMAT_420_OPAQUE                              = 106
    DXGI_FORMAT_YUY2                                    = 107
    DXGI_FORMAT_Y210                                    = 108
    DXGI_FORMAT_Y216                                    = 109
    DXGI_FORMAT_NV11                                    = 110
    DXGI_FORMAT_AI44                                    = 111
    DXGI_FORMAT_IA44                                    = 112
    DXGI_FORMAT_P8                                      = 113
    DXGI_FORMAT_A8P8                                    = 114
    DXGI_FORMAT_B4G4R4A4_UNORM                          = 115
    DXGI_FORMAT_P208                                    = 130
    DXGI_FORMAT_V208                                    = 131
    DXGI_FORMAT_V408                                    = 132
    DXGI_FORMAT_SAMPLER_FEEDBACK_MIN_MIP_OPAQUE         = 189
    DXGI_FORMAT_SAMPLER_FEEDBACK_MIP_REGION_USED_OPAQUE = 190
    DXGI_FORMAT_FORCE_UINT                              = 0xffffffff

class DDSPixelFormat:
    def __init__(self):
        self.dwSize   = 32
        self.dwFlags = 0x41
        self.dwFourCC = b'\x00\x00\x00\x00'
        self.dwRGBBitCount = 32;
        self.dwRBitMask    = 0x00FF0000
        self.dwGBitMask    = 0x0000FF00
        self.dwBBitMask    = 0x000000FF
        self.dwABitMask    = 0xFF000000

    def set_compression(self, fourCC):
        if fourCC is not None:
            self.dwFlags = 0x04
            self.dwFourCC = fourCC
            self.dwRGBBitCount = 0
            self.dwRBitMask    = 0
            self.dwGBitMask    = 0
            self.dwBBitMask    = 0
            self.dwABitMask    = 0
        else:
            self.dwFlags = 0x41
            self.dwFourCC = b'\x00\x00\x00\x00'
            self.dwRGBBitCount = 0x20
            self.dwRBitMask    = 0x00FF0000
            self.dwGBitMask    = 0x0000FF00
            self.dwBBitMask    = 0x000000FF
            self.dwABitMask    = 0xFF000000
    
    def exbip_rw(self, rw):
        self.dwSize        = rw.rw_uint32(self.dwSize)
        self.dwFlags       = rw.rw_uint32(self.dwFlags)
        self.dwFourCC      = rw.rw_bytestring(self.dwFourCC, 4)
        self.dwRGBBitCount = rw.rw_uint32(self.dwRGBBitCount)
        self.dwRBitMask    = rw.rw_uint32(self.dwRBitMask)
        self.dwGBitMask    = rw.rw_uint32(self.dwGBitMask)
        self.dwBBitMask    = rw.rw_uint32(self.dwBBitMask)
        self.dwABitMask    = rw.rw_uint32(self.dwABitMask)

class DDSHeader:
    def __init__(self):
        self.dwSize  = 124
        self.dwFlags = 0x1007
        
        self.dwHeight = 0
        self.dwWidth = 0
        self.dwPitchOrLinearSize = 0
        self.dwDepth = 0
        self.dwMipMapCount = 1
        self.dwReserved1 = [0 for _ in range(11)]
        self.ddspf = DDSPixelFormat()
        self.dwCaps  = 0x1000
        self.dwCaps2 = 0
        self.dwCaps3 = 0
        self.dwCaps4 = 0
        self.dwReserved2 = 0
    
    def exbip_rw(self, rw):
        self.dwSize              = rw.rw_uint32(self.dwSize)
        self.dwFlags             = rw.rw_uint32(self.dwFlags)
        self.dwHeight            = rw.rw_uint32(self.dwHeight)
        self.dwWidth             = rw.rw_uint32(self.dwWidth)
        self.dwPitchOrLinearSize = rw.rw_uint32(self.dwPitchOrLinearSize)
        self.dwDepth             = rw.rw_uint32(self.dwDepth)
        self.dwMipMapCount       = rw.rw_uint32(self.dwMipMapCount)
        self.dwReserved1         = rw.rw_uint32s(self.dwReserved1, 11)
        rw.rw_obj(self.ddspf)
        self.dwCaps              = rw.rw_uint32(self.dwCaps)
        self.dwCaps2             = rw.rw_uint32(self.dwCaps2)
        self.dwCaps3             = rw.rw_uint32(self.dwCaps3)
        self.dwCaps4             = rw.rw_uint32(self.dwCaps4)
        self.dwReserved2         = rw.rw_uint32(self.dwReserved2)
    
    def set_properties(self, width, height, fourCC, mipmap_count):
        self.dwWidth       = width
        self.dwHeight      = height
        self.dwMipMapCount = mipmap_count
        
        self.dwFlags = 0x1007
        if fourCC is not None:
            # self.dwFlags |= 0x80000
            blocksize = 0x08 if fourCC == b'DXT1' else 0x10
            # self.dwPitchOrLinearSize = max( 1, ((self.width+3)//4) ) * blocksize
            self.ddspf.set_compression(fourCC)
        
        if mipmap_count > 1:
            self.dwFlags |= 0x20000
            self.dwCaps  |= 0x400000


class DDSExtendedHeader:
    def __init__(self):
        self.dxgiFormat        = 0
        self.resourceDimension = 0
        self.miscFlag          = 0
        self.arraySize         = 0
        self.miscFlags2        = 0
    
    def exbip_rw(self, rw):
        self.dxgiFormat        = rw.rw_uint32(self.dxgiFormat)
        self.resourceDimension = rw.rw_uint32(self.resourceDimension)
        self.miscFlag          = rw.rw_uint32(self.miscFlag)
        self.arraySize         = rw.rw_uint32(self.arraySize)
        self.miscFlags2        = rw.rw_uint32(self.miscFlags2)

class DDS(DSCSSerializable):
    def __init__(self):
        self.dwMagic = b'DDS '
        self.header  = DDSHeader()
        self.extended_header = DDSExtendedHeader()
        self.payload = b''
    
    def mipmap_size(self, level):
        fourCC = self.header.ddspf.dwFourCC
        
        width  = self.header.dwWidth
        height = self.header.dwHeight
        depth  = self.header.dwDepth
        
        
        if fourCC == b'\x00\x00\x00\x00':
            if self.header.dwFlags & 0x800000:
                raw_size = width * height * depth * ((self.header.ddspf.dwRGBBitCount + 7)//8)
            else:
                raw_size = width * height * ((self.header.ddspf.dwRGBBitCount + 7)//8)
                
        elif fourCC == b'q\x00\x00\x00':
            if self.header.dwFlags & 0x800000:
                raw_size = width * height * depth * 8
            else:
                raw_size = width * height * 8
                
        elif fourCC == b'DXT1':
            raw_size = width * height // 2
        elif fourCC == b'DXT3':
            raw_size = width * height
        elif fourCC == b'DXT5':
            raw_size = width * height
        elif fourCC == b'DX10':
            # Assume DXT for now...
            raw_size = width * height
            dxgi_format = self.extended_header.dxgiFormat
            
            if   dxgi_format == DXGIFormat.DXGI_FORMAT_BC1_TYPELESS:   raw_size //= 2
            elif dxgi_format == DXGIFormat.DXGI_FORMAT_BC1_UNORM:      raw_size *= 3
            elif dxgi_format == DXGIFormat.DXGI_FORMAT_BC1_UNORM_SRGB: raw_size *= 3
            elif dxgi_format == DXGIFormat.DXGI_FORMAT_BC2_TYPELESS:   raw_size //= 2
            elif dxgi_format == DXGIFormat.DXGI_FORMAT_BC2_UNORM:      raw_size *= 3
            elif dxgi_format == DXGIFormat.DXGI_FORMAT_BC2_UNORM_SRGB: raw_size *= 3
            elif dxgi_format == DXGIFormat.DXGI_FORMAT_BC3_TYPELESS:   pass
            elif dxgi_format == DXGIFormat.DXGI_FORMAT_BC3_UNORM:      raw_size *= 6
            elif dxgi_format == DXGIFormat.DXGI_FORMAT_BC3_UNORM_SRGB: raw_size *= 6
            elif dxgi_format == DXGIFormat.DXGI_FORMAT_BC4_TYPELESS:   pass
            elif dxgi_format == DXGIFormat.DXGI_FORMAT_BC4_UNORM:      raw_size *= 6
            elif dxgi_format == DXGIFormat.DXGI_FORMAT_BC4_SNORM:      raw_size *= 6
            elif dxgi_format == DXGIFormat.DXGI_FORMAT_BC5_TYPELESS:   pass
            elif dxgi_format == DXGIFormat.DXGI_FORMAT_BC5_UNORM:      raw_size *= 6
            elif dxgi_format == DXGIFormat.DXGI_FORMAT_BC5_SNORM:      raw_size *= 6
            # elif dxgi_format == DXGIFormat.DXGI_FORMAT_B5G6R5_UNORM:   pass
            # elif dxgi_format == DXGIFormat.DXGI_FORMAT_B5G5R5A1_UNORM: pass
            # elif dxgi_format == DXGIFormat.DXGI_FORMAT_B8G8R8A8_UNORM: pass
            # elif dxgi_format == DXGIFormat.DXGI_FORMAT_B8G8R8X8_UNORM: pass
            # elif dxgi_format == DXGIFormat.DXGI_FORMAT_R10G10B10_XR_BIAS_A2_UNORM: pass
            # elif dxgi_format == DXGIFormat.DXGI_FORMAT_B8G8R8A8_TYPELESS:   pass
            # elif dxgi_format == DXGIFormat.DXGI_FORMAT_B8G8R8A8_UNORM_SRGB: pass
            # elif dxgi_format == DXGIFormat.DXGI_FORMAT_B8G8R8X8_TYPELESS:   pass
            # elif dxgi_format == DXGIFormat.DXGI_FORMAT_B8G8R8X8_UNORM_SRGB: pass
        
            # elif dxgi_format == DXGIFormat.DXGI_FORMAT_BC6H_TYPELESS:  pass
            # elif dxgi_format == DXGIFormat.DXGI_FORMAT_BC6H_UF16:      pass
            # elif dxgi_format == DXGIFormat.DXGI_FORMAT_BC6H_SF16:      pass
            elif dxgi_format == DXGIFormat.DXGI_FORMAT_BC7_TYPELESS:   pass
            elif dxgi_format == DXGIFormat.DXGI_FORMAT_BC7_UNORM:      raw_size *= 6
            elif dxgi_format == DXGIFormat.DXGI_FORMAT_BC7_UNORM_SRGB: raw_size *= 6
        else:
            raise ValueError(f"Unrecognised fourCC: {fourCC}")
        
        raw_size //= ((level + 1) * (level + 1))
        
        return raw_size
    
    def payload_size(self):
        size = 0
        raw_size = self.mipmap_size(0)
        mipcount = self.header.dwMipMapCount if self.header.dwFlags & 0x20000 else 1
        for i in range(mipcount):
            texlevel = i+1
            size += raw_size // (texlevel*texlevel)
        
        return size
    
    def exbip_rw(self, rw):
        self.dwMagic = rw.rw_bytestring(self.dwMagic, 4)
        if self.dwMagic != b'DDS ':
            raise ValueError("Not a DDS file")
        
        rw.rw_obj(self.header)
        if self.header.ddspf.dwFourCC == b'DX10':
            rw.rw_obj(self.extended_header)
        
        self.payload = rw.rw_bytestring(self.payload, self.payload_size())
        
        rw.assert_eof()

def to_nonsrgb_dds(dds):
    srgb = False
    
    if dds.header.ddspf.dwFourCC != b'DX10':
        return srgb
    
    dxgi_format = dds.extended_header.dxgiFormat
    
    if dxgi_format == DXGIFormat.DXGI_FORMAT_BC1_UNORM or dxgi_format == DXGIFormat.DXGI_FORMAT_BC1_UNORM_SRGB:
        if dxgi_format == DXGIFormat.DXGI_FORMAT_BC1_UNORM_SRGB: srgb = True
        
        dds.header.ddspf.dwFourCC = b"DXT1"
    
    elif dxgi_format == DXGIFormat.DXGI_FORMAT_BC2_UNORM or dxgi_format == DXGIFormat.DXGI_FORMAT_BC2_UNORM_SRGB:
        if dxgi_format == DXGIFormat.DXGI_FORMAT_BC2_UNORM_SRGB: srgb = True
        
        dds.header.ddspf.dwFourCC = b"DXT3" # Difference with DXT
    
    elif dxgi_format == DXGIFormat.DXGI_FORMAT_BC3_UNORM or dxgi_format == DXGIFormat.DXGI_FORMAT_BC3_UNORM_SRGB:
        if dxgi_format == DXGIFormat.DXGI_FORMAT_BC3_UNORM_SRGB: srgb = True
        
        dds.header.ddspf.dwFourCC = b"DXT5"
    
    elif dxgi_format == DXGIFormat.DXGI_FORMAT_BC7_UNORM_SRGB:
        dds.extended_header.dxgiFormat= DXGIFormat.DXGI_FORMAT_BC7_UNORM
        srgb = True
    
    return srgb

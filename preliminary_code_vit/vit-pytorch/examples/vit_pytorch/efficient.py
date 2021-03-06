import torch
from einops import rearrange, repeat
from torch import nn

class ViT(nn.Module):
    def __init__(self, *, image_size, patch_size, num_classes, dim, transformer, pool = 'cls', channels = 3):
        super().__init__()
        assert image_size % patch_size == 0, 'image dimensions must be divisible by the patch size'
        assert pool in {'cls', 'mean'}, 'pool type must be either cls (cls token) or mean (mean pooling)'
        num_patches = (image_size // patch_size) ** 2
        patch_dim = channels * patch_size ** 2  # 每一个patch块的有多少个像素

        self.patch_size = patch_size
# 学习一下这个位置编码. 好像跟swin不一样.
        self.pos_embedding = nn.Parameter(torch.randn(1, num_patches + 1, dim)) # shape:1,50,128
        self.patch_to_embedding = nn.Linear(patch_dim, dim)
        self.cls_token = nn.Parameter(torch.randn(1, 1, dim))
        self.transformer = transformer

        self.pool = pool
        self.to_latent = nn.Identity()

        self.mlp_head = nn.Sequential(
            nn.LayerNorm(dim),
            nn.Linear(dim, num_classes)
        )

    def forward(self, img):
        p = self.patch_size # 每一个patch 是32*32的

        x = rearrange(img, 'b c (h p1) (w p2) -> b (h w) (p1 p2 c)', p1 = p, p2 = p)# 图片拉直.
        x = self.patch_to_embedding(x) #  x: 1, 49, 3072  batchsize, 49个patch,dimension
        b, n, _ = x.shape

        cls_tokens = repeat(self.cls_token, '() n d -> b n d', b = b)
        x = torch.cat((cls_tokens, x), dim=1) # 在开始部分加入一个cls的编码.
        x += self.pos_embedding[:, :(n + 1)]
        x = self.transformer(x)
# 下面运算用poll 把patch mean掉.
        x = x.mean(dim = 1) if self.pool == 'mean' else x[:, 0]

        x = self.to_latent(x)
        return self.mlp_head(x)

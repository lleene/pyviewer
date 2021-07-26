from imageloader import ImageLoader

loader = ImageLoader()
loader.loadMedia("/mnt/media/Media/doujin_archive_2")
file_list = loader.loadViews()
loader.orderFileList(file_list)

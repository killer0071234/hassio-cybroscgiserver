import hashlib
import os

import PIL.Image
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.templatetags.static import static

from project.main.models import Plant, get_default_page


class FileInfo:
    filename = ""
    filepath = ""
    size = ""
    is_dir = False
    link = ""


class ImgFileInfo(FileInfo):
    def get_thumb(self):
        fname = get_thumb_filehash(self.filepath)
        thumb_path = get_thumb_path()

        path = os.path.join(thumb_path, fname)
        if not os.path.exists(path):
            try:
                PIL.Image.init()
                size = (120, 90)

                img = PIL.Image.open(self.filepath)
                if img.mode != "RGB":
                    img = img.convert("RGB")

                w, h = size
                img_w, img_h = img.size

                if img_w < img_h:
                    h = int((float(img_h) / float(img_w)) * w)
                    size = (w, h)

                img.thumbnail(size, PIL.Image.Resampling.LANCZOS)
                os.makedirs(thumb_path, exist_ok=True)
                img.save(path)
            except Exception as ex:
                return static('img/no_image_thumb.gif')

        return os.path.join(settings.DATA_URL, 'thumbs', fname)


def get_thumb_path() -> str:
    return os.path.normpath(settings.MMANAGER_THUMBS_ROOT)


def get_thumb_filehash(filepath: str) -> str:
    _, ext = os.path.splitext(filepath)
    return hashlib.sha1(filepath.encode()).hexdigest()[0:20] + ext


@login_required
def create_list(request, plant=None, edit_mode=False):
    homepages = []
    filter_dirs = False

    if plant is not None:
        page = plant.homepage
        plant_id = plant.id
        data_root = plant.homepage.get_data_folder()
        homepages.append(data_root.strip("/"))
    else:
        page = get_default_page()
        plant_id = 0
        data_root = "./"

        if not (request.user.permissions.is_server_admin or
                request.user.permissions.can_manage_site_content or
                request.user.permissions.can_manage_plants):
            for p in Plant.objects.filter(admins__in = [request.user]):
                homepages.append(p.homepage.get_data_folder().strip("/"))

        if len(homepages) == 1:
            data_root = homepages[0]

    if len(homepages) == 1:
        filter_dirs = False

    data_folder = page.get_data_folder()
    use_default = True

    data_root_full = os.path.normpath(os.path.join(settings.DATA_FOLDER_ROOT,
                                                   data_root))
    media_root_full = os.path.normpath(settings.DATA_FOLDER_ROOT) + "/"

    if "current_path" in request.session:
        current_path = request.session.get("current_path", "")
        current_path_full = os.path.normpath(os.path.join(
            settings.DATA_FOLDER_ROOT, current_path
        ))
        show_parent_dir = len(current_path_full) > len(data_root_full)
        data_folder = request.session.get("current_path", "")
        path = os.path.normpath(os.path.join(settings.DATA_FOLDER_ROOT,
                                             data_folder))
        use_default = not os.path.exists(path)

    if use_default:
        if len(homepages) == 1:
            data_folder = homepages[0] + "/"
            filter_dirs = False
        else:
            data_folder = page.get_data_folder()
        path = os.path.normpath(os.path.join(settings.DATA_FOLDER_ROOT,
                                             data_folder))
        show_parent_dir = False

    filter_dirs = (path == media_root_full) and not (
        show_parent_dir or
        request.user.permissions.is_server_admin or
        request.user.permissions.can_manage_site_content or
        request.user.permissions.can_manage_plants
    )

    if request.method == "POST":
        operation = request.POST.get("operation", "")

        if edit_mode and operation == "upload":
            # upload new files
            for i in range(int(request.POST.get("file_count", "0"))):
                filename = f"file_{i}"
                if filename in request.FILES:
                    f = request.FILES[filename]
                    file_content = f.read()
                    try:
                        filepath = os.path.join(path, f.name)
                        destination = open(filepath, 'wb+')
                        destination.write(file_content)
                        destination.close()

                        # delete thumb if exists
                        thumb_filepath = os.path.join(
                            get_thumb_path(),
                            get_thumb_filehash(filepath)
                        )
                        if os.path.exists(thumb_filepath):
                            try:
                                os.remove(thumb_filepath)
                            except:
                                pass
                    except:
                        pass

        elif edit_mode and operation == "filelist":
            # delete selected files
            # loop through regular files
            for i in range(int(request.POST.get("file_count", "0"))):
                if request.POST.get("f_sel_%i" % i, "") != "":
                    os.remove(os.path.join(
                        path, request.POST.get("f_name_%i" % i, "")
                    ))

            # loop through images
            for i in range(int(request.POST.get("img_count", "0"))):
                if request.POST.get("img_sel_%i" % i, "") != "":
                    filepath = os.path.join(
                        path, request.POST.get("img_name_%i" % i, "")
                    )
                    thumb_filepath = os.path.join(
                        get_thumb_path(),
                        get_thumb_filehash(filepath)
                    )

                    try:
                        os.remove(filepath)
                    except:
                        pass

                    try:
                        os.remove(thumb_filepath)
                    except:
                        pass

        elif operation == "change_dir":
            request.session["current_path"] = request.POST.get("param", "")

        return HttpResponseRedirect(
            "/mmanager/list/"
            if edit_mode
            else f"/mmanager/select_image/{plant_id}/"
        )

    # get all files in directory and sort it
    f_list = [f for f in os.listdir(path)]
    f_list.sort()

    dirs = []
    files = []
    images = []

    # loop through file list and decide what type it is
    for f in f_list:
        info = None
        p = os.path.normpath(os.path.join(path, f))
        # is it directory?
        if os.path.isdir(p):
            if len(f) != 0 and f[0] != '.':
                try:
                    # add only allowed directories
                    if filter_dirs:
                        homepages.index(f)
                    info = FileInfo()
                    info.is_dir = True
                    info.filepath = data_folder + f + "/"
                    dirs.append(info)
                except:
                    pass
        else:
            # is it image?
            basename, ext = os.path.splitext(f)
            if ext.lower() in [".jpg", ".jpeg", ".png", ".gif"]:
                info = ImgFileInfo()
                images.append(info)
            else:
                # if nothing else, it's regular file
                info = FileInfo()
                files.append(info)

            # get file size only for images and files
            info.size = "%.1f kB" % (
                os.path.getsize(os.path.join(path, f)) / 1024.0
            )
            # create preview link too
            info.link = os.path.join(settings.DATA_URL,
                                     'media',
                                     data_folder,
                                     f)
            info.filepath = os.path.normpath(os.path.join(path, f))

        # this is the common data for all type of files (and directories)
        if info is not None:
            info.filename = f

    parent_dir = os.path.normpath(data_folder + "../") + "/" \
        if show_parent_dir \
        else ""
    template = "list.html" if edit_mode else "select_image.html"

    return render(
        request,
        "mmanager/" + template,
        {
            "plant": plant,
            "plant_id": plant_id,
            "dir_count": len(dirs),
            "file_count": len(files),
            "img_count": len(images),
            "dirs": dirs,
            "files": files,
            "images": images,
            "show_parent_dir": show_parent_dir,
            "parent_dir": parent_dir,
            "rw_access": edit_mode,
            "edit_mode": edit_mode,
            "active_menu": "mmanager",
            "data_folder": data_folder.rstrip("/"),
        }
    )


@login_required
def list_media(request):
    return create_list(request, edit_mode=True)


@login_required
def select_image(request, plant_id):
    try:
        plant = Plant.objects.get(id=plant_id)
    except Plant.DoesNotExist:
        plant = None

    return create_list(request, plant=plant, edit_mode=False)

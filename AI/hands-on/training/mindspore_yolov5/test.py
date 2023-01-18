ckpt_file="trial.mindir"

# Taking ckpt file by looking its extension, otherwise it takes latest one in the folder
if ckpt_file[-4:] == 'ckpt':
    print(f'Your .ckpt File is {ckpt_file}')
    pass
elif ckpt_file[-4:] == 'ndir':
    print(f'Your .mindir File is {ckpt_file}')
else:
    ckpt_file = sorted(glob(f'{ckpt_file}/*.ckpt'), key=os.path.getmtime)[-1]
    print(f'Your .ckpt Folder is {ckpt_file}')
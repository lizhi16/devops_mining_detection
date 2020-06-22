### gvisor-1.0.tar.gz :

**Listen_modified_addr(t \*Task, at usermem.AccessType)**

- `function-1`: get addr from syscall 308 and clear the permission of this addr 

**handle_seg_faults()**

- `function-2`: return permissions of the addr

### Modified Contents:

- `pkg/sentry/kernel/task_run.go#395-466`

- `pkg/sentry/mm/syscall.go#395-466#40-58`

### Test Docker Image:

- `docker run -it --runtime=runsc --memory=4000m cloudinsky/gvisor-sys:v2`

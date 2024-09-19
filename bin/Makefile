clean:
	rm -rf save3ds

deps:
	[ ! -d 'save3ds' ] && git clone https://github.com/wwylele/save3ds
	cd save3ds && cargo build --no-default-features --release

all: deps
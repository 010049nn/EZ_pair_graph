.PHONY: build run plot clean

# Build Docker image
build:
	docker build -t ez_pair_graph .

# Start interactive shell
run:
	docker run -it --rm \
		-v $$(pwd)/data:/data \
		-v $$(pwd)/output_EZ:/app/output_EZ \
		ez_pair_graph

# Run pipeline with input file (usage: make plot FILE=data/input.txt)
plot:
	docker run --rm \
		-v $$(pwd)/data:/data \
		-v $$(pwd)/output_EZ:/app/output_EZ \
		ez_pair_graph \
		bash ./pipeline_for_EZ_plot.sh /data/$$(basename $(FILE)) $(OPTS)

# Run with test dataset
test:
	docker run --rm \
		-v $$(pwd)/output_EZ:/app/output_EZ \
		ez_pair_graph \
		bash ./pipeline_for_EZ_plot.sh test_dataset.txt

# Clean up Docker image
clean:
	docker rmi ez_pair_graph 2>/dev/null || true

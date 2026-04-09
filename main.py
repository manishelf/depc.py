import sys
import depc


def main():
    if len(sys.argv) < 2:
        processor = depc.Processor(depc.Repl())
    else:
        print("processing ", sys.argv[1])
        pre_processor = depc.PreProcessor(sys.argv[1])
        processor = depc.Processor(pre_processor)

        for row in pre_processor:
            print(row)
        print("--------------")

    out = processor.out()
    print("out ", out)


if __name__ == "__main__":
    main()

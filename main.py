import sys
import io
import depc

def main():
    if len(sys.argv) < 2 :
        print("file required for processing"); 
        return
    
    print("processing ", sys.argv[1])

    pre_processor = depc.PreProcessor(sys.argv[1])
    for row in pre_processor:
        print(row)
    
    print("--------------")

    processor = depc.Processor(pre_processor)
    out = processor.out()
    #for res in out:
        #print(res)
         
if __name__ == "__main__":
    main()

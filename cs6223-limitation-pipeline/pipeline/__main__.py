import sys

if len(sys.argv) > 1 and sys.argv[1] == 'limitset':
    from pipeline.limitset import main
    main(sys.argv[2:])
else:
    from pipeline.run import main
    main()
